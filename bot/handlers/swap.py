"""
bot/handlers/swap.py — Handler Tukar Antar Jaringan / OTC Convert (Bot 3 Feature)
===================================================================================
Alur Transaksi Convert/Swap (FULL OTOMATIS — tanpa verifikasi admin):
1. Buyer memilih koin/jaringan asal (misal SOL Solana).
2. Buyer memilih koin/jaringan tujuan (misal ETH Base).
3. Buyer memasukkan nominal koin asal dan alamat wallet tujuan (ETH Base buyer).
4. Bot membuat Quote (Expiry 30 Menit) dengan Fee Convert Tier (Min Rp 6.000, Max Rp 600.000).
5. Bot memberikan alamat deposit hot wallet seller (Solana seller).
6. Buyer menukar koin & memasukkan TX Hash deposit (atau auto-scan riwayat wallet).
7. Bot memverifikasi deposit ON-CHAIN secara otomatis (services.tx_verifier)
   -> Status `CRYPTO_CONFIRMED` & notif user.
8. Bot mengeksekusi payout otomatis koin tujuan ke wallet buyer
   -> Status `COMPLETED` + link Explorer + notif user.
9. Admin hanya menerima notifikasi informatif (tanpa tombol approve/reject).
"""

import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from config.settings import settings
from database.connection import SessionLocal
from database.models import User, Order, AuditLog
from services.price_service import price_service
from services.fee_service import calculate_fee_idr
from services.crypto_sender import CryptoSenderFactory
from services import tx_verifier
from services.detector import deposit_detector
from bot.keyboards.main_menu import get_owner_button
from bot.utils.formatter import format_crypto
from bot.utils.telegram_utils import notify_admins

logger = logging.getLogger(__name__)

# State Conversation
SELECT_SRC_SYMBOL, SELECT_SRC_NET, SELECT_TGT_SYMBOL, SELECT_TGT_NET, INPUT_AMOUNT, INPUT_TARGET_ADDR, CONFIRM_SWAP, WAITING_DEPOSIT_HASH = range(8)

SUPPORTED_ASSETS = ["USDT", "USDC", "ETH", "SOL", "BNB", "TRX", "SUI", "TON", "MATIC", "ARB", "AVAX", "KAIA", "BERA", "APT", "HYPE"]

NETWORKS_BY_SYMBOL = {
    "USDT": ["BSC", "POLYGON", "ARB", "TON", "SOLANA", "ETH"],
    "USDC": ["BASE", "ETH", "BSC", "ARB", "SOLANA", "POLYGON"],
    "ETH": ["BASE", "ARB", "OPTIMISM", "ETH", "ROBINHOOD"],
    "SOL": ["SOLANA"],
    "BNB": ["BSC"],
    "TRX": ["TRON"],
    "SUI": ["SUI"],
    "TON": ["TON"],
    "MATIC": ["POLYGON"],
    "ARB": ["ARB"],
    "AVAX": ["AVAX"],
    "KAIA": ["KAIA"],
    "BERA": ["BERA"],
    "APT": ["APTOS"],
    "HYPE": ["HYPEREVM"]
}


async def start_swap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Langkah 1: Mulai alur Swap / Convert — Pilih Koin Asal."""
    query = update.callback_query
    if query:
        await query.answer()

    keyboard = []
    row = []
    for i, symbol in enumerate(SUPPORTED_ASSETS, 1):
        row.append(InlineKeyboardButton(f"🪙 {symbol}", callback_data=f"swap_src_sym_{symbol}"))
        if i % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Batal", callback_data="cancel_swap")])

    text = "🔄 <b>[TUKAR ANTAR JARINGAN / OTC CONVERT]</b>\n\nSilakan pilih <b>Koin Asal</b> yang ingin kamu kirim:"
    
    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        
    return SELECT_SRC_SYMBOL


async def select_src_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    symbol = query.data.replace("swap_src_sym_", "")
    context.user_data["swap_src_symbol"] = symbol

    networks = NETWORKS_BY_SYMBOL.get(symbol, ["BSC"])
    keyboard = [[InlineKeyboardButton(f"🌐 {net}", callback_data=f"swap_src_net_{net}")] for net in networks]
    keyboard.append([InlineKeyboardButton("❌ Batal", callback_data="cancel_swap")])

    await query.edit_message_text(
        f"Koin Asal: <b>{symbol}</b>\n\nSilakan pilih <b>Jaringan Koin Asal</b>:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_SRC_NET


async def select_src_net(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    net = query.data.replace("swap_src_net_", "")
    context.user_data["swap_src_network"] = net

    keyboard = []
    row = []
    for i, symbol in enumerate(SUPPORTED_ASSETS, 1):
        if symbol == context.user_data.get("swap_src_symbol"):
            continue # Bisa koin sama beda jaringan atau koin beda
        row.append(InlineKeyboardButton(f"🎯 {symbol}", callback_data=f"swap_tgt_sym_{symbol}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Batal", callback_data="cancel_swap")])

    await query.edit_message_text(
        f"Koin Asal: <b>{context.user_data['swap_src_symbol']} ({net})</b>\n\nSilakan pilih <b>Koin Tujuan (Target)</b>:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_TGT_SYMBOL


async def select_tgt_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    symbol = query.data.replace("swap_tgt_sym_", "")
    context.user_data["swap_tgt_symbol"] = symbol

    networks = NETWORKS_BY_SYMBOL.get(symbol, ["BSC"])
    keyboard = [[InlineKeyboardButton(f"🌐 {net}", callback_data=f"swap_tgt_net_{net}")] for net in networks]
    keyboard.append([InlineKeyboardButton("❌ Batal", callback_data="cancel_swap")])

    await query.edit_message_text(
        f"Koin Asal: <b>{context.user_data['swap_src_symbol']} ({context.user_data['swap_src_network']})</b>\n"
        f"Koin Tujuan: <b>{symbol}</b>\n\nSilakan pilih <b>Jaringan Koin Tujuan</b>:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_TGT_NET


async def select_tgt_net(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    net = query.data.replace("swap_tgt_net_", "")
    context.user_data["swap_tgt_network"] = net

    src_sym = context.user_data["swap_src_symbol"]
    src_net = context.user_data["swap_src_network"]
    tgt_sym = context.user_data["swap_tgt_symbol"]
    tgt_net = net

    keyboard = [
        [InlineKeyboardButton("🔙 Batal Transaksi", callback_data="cancel_swap")],
        [get_owner_button()]
    ]

    await query.edit_message_text(
        f"🔄 <b>Konfigurasi Convert:</b>\n"
        f"<b>Dari:</b> {src_sym} ({src_net})\n"
        f"<b>Ke:</b> {tgt_sym} ({tgt_net})\n\n"
        f"Silakan masukkan <b>jumlah koin asal</b> yang ingin kamu kirim (atau masukkan estimasi nilai IDR, misal 50000):",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return INPUT_AMOUNT


async def input_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_input = update.message.text.strip().replace(",", ".")
    try:
        val = float(text_input)
        if val <= 0:
            raise ValueError
    except ValueError:
        keyboard = [
            [InlineKeyboardButton("🔙 Batal Transaksi", callback_data="cancel_swap")],
            [get_owner_button()]
        ]
        await update.message.reply_text(
            "❌ Masukkan angka positif yang valid. Contoh: 0.0025 atau 50000",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return INPUT_AMOUNT

    src_sym = context.user_data["swap_src_symbol"]
    src_net = context.user_data["swap_src_network"]
    tgt_sym = context.user_data["swap_tgt_symbol"]
    tgt_net = context.user_data["swap_tgt_network"]

    # Ambil harga koin asal & koin tujuan
    src_price_info = await price_service.get_price(src_sym)
    tgt_price_info = await price_service.get_price(tgt_sym)

    if not src_price_info or not tgt_price_info:
        await update.message.reply_text("❌ Gagal mengambil harga realtime. Silakan coba beberapa saat lagi.")
        return ConversationHandler.END

    src_idr_price = src_price_info["sell_price_idr"]
    tgt_idr_price = tgt_price_info["buy_price_idr"]

    # Jika input berupa nominal IDR (misal >= 1000)
    if val >= 1000:
        nominal_idr = int(val)
        src_amount = nominal_idr / src_idr_price
    else:
        src_amount = val
        nominal_idr = int(src_amount * src_idr_price)

    # Hitung Fee Convert Tier (Min Rp 6.000, Max Rp 600.000)
    try:
        fee_idr = calculate_fee_idr(
            nominal_idr,
            category="CONVERT",
            symbol=tgt_sym,
            network=tgt_net,
            is_outgoing=True
        )
    except ValueError as fee_err:
        keyboard = [
            [InlineKeyboardButton("🔙 Batal Transaksi", callback_data="cancel_swap")],
            [get_owner_button()]
        ]
        await update.message.reply_text(
            f"⚠️ {str(fee_err)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return INPUT_AMOUNT

    # Perhitungan koin tujuan yang diterima
    net_idr_for_target = nominal_idr - fee_idr
    tgt_amount = net_idr_for_target / tgt_idr_price

    context.user_data["swap_src_amount"] = src_amount
    context.user_data["swap_nominal_idr"] = nominal_idr
    context.user_data["swap_fee_idr"] = fee_idr
    context.user_data["swap_tgt_amount"] = tgt_amount

    keyboard = [
        [InlineKeyboardButton("🔙 Batal Transaksi", callback_data="cancel_swap")],
        [get_owner_button()]
    ]

    await update.message.reply_text(
        f"📝 <b>[INPUT WALLET TUJUAN]</b>\n\n"
        f"Kamu akan menukar:\n"
        f"<b>{src_amount:.6f} {src_sym} ({src_net})</b> (~Rp {nominal_idr:,})\n"
        f"Fee Convert: <b>Rp {fee_idr:,}</b>\n"
        f"Estimasi yang diterima: <b>{tgt_amount:.6f} {tgt_sym} ({tgt_net})</b>\n\n"
        f"Silakan masukkan <b>Alamat Wallet {tgt_sym} ({tgt_net})</b> tujuan milikmu:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return INPUT_TARGET_ADDR


async def input_target_addr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_addr = update.message.text.strip()
    tgt_net = context.user_data["swap_tgt_network"]

    # Validasi alamat wallet tujuan
    sender = CryptoSenderFactory.get_sender(tgt_net)
    if not sender.validate_address(target_addr):
        keyboard = [
            [InlineKeyboardButton("🔙 Batal Transaksi", callback_data="cancel_swap")],
            [get_owner_button()]
        ]
        await update.message.reply_text(
            f"❌ Format alamat wallet {tgt_net} tidak valid! Silakan periksa kembali dan masukkan ulang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return INPUT_TARGET_ADDR

    context.user_data["swap_target_addr"] = target_addr

    src_sym = context.user_data["swap_src_symbol"]
    src_net = context.user_data["swap_src_network"]
    src_amount = context.user_data["swap_src_amount"]
    tgt_sym = context.user_data["swap_tgt_symbol"]
    tgt_amount = context.user_data["swap_tgt_amount"]
    nominal_idr = context.user_data["swap_nominal_idr"]
    fee_idr = context.user_data["swap_fee_idr"]

    # Ambil deposit wallet seller
    src_sender = CryptoSenderFactory.get_sender(src_net)
    seller_deposit_wallet = getattr(src_sender, "wallet_address", settings.EVM_WALLET_ADDRESS)

    context.user_data["swap_seller_deposit_wallet"] = seller_deposit_wallet

    keyboard = [
        [InlineKeyboardButton("✅ Ya, Konfirmasi & Dapatkan Alamat Setor", callback_data="confirm_swap_order")],
        [InlineKeyboardButton("❌ Batal", callback_data="cancel_swap")]
    ]

    await update.message.reply_text(
        f"📑 <b>[RINGKASAN QUOTE CONVERT]</b>\n"
        f"<i>Masa berlaku quote: 30 Menit</i>\n\n"
        f"<b>Kirim:</b> {src_amount:.6f} {src_sym} ({src_net})\n"
        f"<b>Nilai IDR:</b> Rp {nominal_idr:,}\n"
        f"<b>Fee Convert:</b> Rp {fee_idr:,}\n"
        f"<b>Terima:</b> ~{tgt_amount:.6f} {tgt_sym} ({tgt_net})\n"
        f"<b>Wallet Tujuan:</b> <code>{target_addr}</code>\n\n"
        f"Apakah data di atas sudah sesuai?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CONFIRM_SWAP


async def confirm_swap_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    order_id = f"SWAP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{telegram_id % 1000:03d}"

    src_sym = context.user_data["swap_src_symbol"]
    src_net = context.user_data["swap_src_network"]
    src_amount = context.user_data["swap_src_amount"]
    tgt_sym = context.user_data["swap_tgt_symbol"]
    tgt_net = context.user_data["swap_tgt_network"]
    tgt_amount = context.user_data["swap_tgt_amount"]
    nominal_idr = context.user_data["swap_nominal_idr"]
    fee_idr = context.user_data["swap_fee_idr"]
    target_addr = context.user_data["swap_target_addr"]
    seller_deposit_wallet = context.user_data["swap_seller_deposit_wallet"]

    quoted_at = datetime.utcnow()
    expires_at = quoted_at + timedelta(minutes=30)

    db = SessionLocal()
    try:
        # User record
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=query.from_user.username,
                full_name=query.from_user.full_name
            )
            db.add(user)
            db.commit()

        # Create Order
        order = Order(
            order_id=order_id,
            telegram_id=telegram_id,
            order_type="swap",
            crypto_symbol=src_sym,
            network=src_net,
            crypto_amount=src_amount,
            target_crypto_symbol=tgt_sym,
            target_network=tgt_net,
            target_crypto_amount=tgt_amount,
            price_per_unit=0,
            nominal_idr=nominal_idr,
            fee_idr=fee_idr,
            total_idr=nominal_idr,
            fee_category="CONVERT",
            buyer_wallet=target_addr,
            deposit_wallet=seller_deposit_wallet,
            status="WAITING_CRYPTO_DEPOSIT",
            quoted_at=quoted_at,
            quote_expires_at=expires_at
        )
        db.add(order)
        
        audit = AuditLog(
            telegram_id=telegram_id,
            action="CREATE_SWAP_ORDER",
            order_id=order_id,
            from_status="DRAFT",
            to_status="WAITING_CRYPTO_DEPOSIT",
            details=f"Convert {src_amount} {src_sym} ({src_net}) -> {tgt_amount} {tgt_sym} ({tgt_net})"
        )
        db.add(audit)
        db.commit()

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating swap order: {e}")
        await query.edit_message_text("❌ Gagal membuat order swap. Silakan coba lagi.")
        db.close()
        return ConversationHandler.END
    finally:
        db.close()

    context.user_data["active_swap_order_id"] = order_id

    keyboard = [
        [InlineKeyboardButton("🔗 Masukkan TX Hash / Bukti Setor", callback_data=f"input_swap_tx_{order_id}")],
        [InlineKeyboardButton("❌ Batal Order", callback_data=f"cancel_swap_order_{order_id}")]
    ]

    await query.edit_message_text(
        f"✅ <b>ORDER CONVERT BERHASIL DIBUAT!</b>\n"
        f"<b>ID Order:</b> <code>{order_id}</code>\n"
        f"<b>Batas Waktu Quote:</b> 30 Menit\n\n"
        f"📌 <b>INSTRUKSI SETORAN DANA:</b>\n"
        f"Silakan kirim tepat <code>{src_amount:.6f}</code> <b>{src_sym} ({src_net})</b> ke alamat wallet seller berikut:\n\n"
        f"<code>{seller_deposit_wallet}</code>\n\n"
        f"Setelah mengirim, tekan tombol di bawah ini untuk memasukkan TX Hash atau foto bukti pengirimanmu:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAITING_DEPOSIT_HASH


async def prompt_input_tx_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = query.data.replace("input_swap_tx_", "")
    context.user_data["active_swap_order_id"] = order_id

    keyboard = [
        [InlineKeyboardButton("❌ Batal Order", callback_data=f"cancel_swap_order_{order_id}")],
        [get_owner_button()]
    ]

    await query.edit_message_text(
        f"🔗 <b>INPUT TX HASH / BUKTI SETOR CONVERT</b>\n\n"
        f"ID Order: <code>{order_id}</code>\n\n"
        f"Silakan kirimkan <b>TX Hash (Hash Transaksi)</b> atau <b>Foto Screenshot Bukti Pengiriman</b> ke chat bot ini:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAITING_DEPOSIT_HASH


async def input_deposit_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_id = context.user_data.get("active_swap_order_id")
    if not order_id and update.callback_query:
        order_id = update.callback_query.data.replace("input_swap_tx_", "")

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.order_id == order_id).first() if order_id else None
        if not order:
            await update.message.reply_text("❌ Order tidak ditemukan atau sudah kadaluarsa.")
            return ConversationHandler.END

        deposit_proof = ""
        photo_file_id = None

        if update.message and update.message.photo:
            photo_file_id = update.message.photo[-1].file_id
            deposit_proof = f"PHOTO:{photo_file_id}"
        elif update.message and update.message.text:
            deposit_proof = update.message.text.strip()
        else:
            await update.message.reply_text("⚠️ Silakan kirimkan teks TX Hash atau unggah foto screenshot bukti transfer.")
            return WAITING_DEPOSIT_HASH

        # Simpan bukti. Status tetap WAITING_CRYPTO_DEPOSIT hingga
        # deposit terverifikasi on-chain (bypass verifikasi admin).
        order.deposit_tx_hash = deposit_proof
        db.commit()

        # --- Verifikasi on-chain langsung (respons instan) ---
        verified_result = None
        if not deposit_proof.startswith("PHOTO:"):
            verified_result = await tx_verifier.verify_deposit(
                network=order.network,
                symbol=order.crypto_symbol,
                tx_hash=deposit_proof,
                expected_wallet=order.deposit_wallet,
                expected_amount=float(order.crypto_amount),
            )

        menu_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu Utama", callback_data="menu_back")]])
        if verified_result and verified_result.get("verified"):
            # Konfirmasi + eksekusi payout otomatis (kirim koin tujuan)
            # Pesan status verifikasi dan hasil convert dikirimkan oleh deposit_detector._confirm_order
            await deposit_detector._confirm_order(
                db, order, deposit_proof, verified_result, context.application
            )
        else:
            # Belum terlihat di chain -> detector akan memverifikasi ulang otomatis
            await _notify_admin_deposit_pending(order, deposit_proof, photo_file_id, context)
            await update.message.reply_text(
                f"📥 <b>Bukti Setoran Diterima!</b>\n\n"
                f"ID Order: <code>{order.order_id}</code>\n"
                f"TX Hash: <code>{deposit_proof}</code>\n\n"
                f"🔍 Deposit sedang <b>diverifikasi otomatis</b> di blockchain "
                f"(maksimal ±2 menit). Setelah terverifikasi, koin tujuan "
                f"<b>{order.target_crypto_symbol} ({order.target_network})</b> "
                f"akan langsung dikirim ke walletmu — <b>tanpa konfirmasi admin</b>.",
                parse_mode="HTML",
                reply_markup=menu_keyboard
            )
    except Exception as e:
        db.rollback()
        logger.error(f"Error handling deposit proof for swap: {e}", exc_info=True)
        await update.message.reply_text("❌ Terjadi kesalahan saat menyimpan bukti transfer.")
    finally:
        db.close()

    return ConversationHandler.END


async def _notify_admin_deposit_pending(order, deposit_proof, photo_file_id, context):
    """Notifikasi informatif ke admin (tanpa tombol approve — flow full otomatis)."""
    try:
        admin_msg = (
            f"📥 <b>[DEPOSIT MENUNGGU VERIFIKASI OTOMATIS]</b>\n\n"
            f"ID Order: <code>{order.order_id}</code>\n"
            f"User: <code>{order.telegram_id}</code>\n"
            f"Deposit: {order.crypto_amount} {order.crypto_symbol} ({order.network})\n"
            f"Tujuan: {order.target_crypto_amount} {order.target_crypto_symbol} "
            f"({order.target_network})\n"
            f"Bukti/TX Hash: <code>{deposit_proof}</code>\n\n"
            f"ℹ️ Deposit akan diverifikasi otomatis di blockchain. "
            f"Jika sudah terverifikasi, koin tujuan akan dikirim otomatis."
        )
        if photo_file_id:
            try:
                await context.bot.send_photo(
                    chat_id=settings.ADMIN_GROUP_ID,
                    photo=photo_file_id,
                    caption=admin_msg,
                    parse_mode="HTML",
                )
            except Exception:
                for admin_id in settings.ADMIN_CHAT_IDS:
                    try:
                        await context.bot.send_photo(
                            chat_id=admin_id,
                            photo=photo_file_id,
                            caption=admin_msg,
                            parse_mode="HTML",
                        )
                    except Exception:
                        pass
        else:
            await notify_admins(context.bot, admin_msg)
    except Exception as admin_err:
        logger.error(f"Error sending admin notification for swap proof: {admin_err}")


async def cancel_swap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        try:
            await query.answer()
        except Exception:
            pass
        from bot.handlers.start import send_main_menu
        await send_main_menu(update, context)
    else:
        await update.message.reply_text(
            text="❌ Sesi convert dibatalkan.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Menu Utama", callback_data="menu_back")
            ]])
        )
    return ConversationHandler.END

swap_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_swap, pattern="^start_swap$")],
    states={
        SELECT_SRC_SYMBOL: [CallbackQueryHandler(select_src_symbol, pattern="^swap_src_sym_")],
        SELECT_SRC_NET: [CallbackQueryHandler(select_src_net, pattern="^swap_src_net_")],
        SELECT_TGT_SYMBOL: [CallbackQueryHandler(select_tgt_symbol, pattern="^swap_tgt_sym_")],
        SELECT_TGT_NET: [CallbackQueryHandler(select_tgt_net, pattern="^swap_tgt_net_")],
        INPUT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_amount)],
        INPUT_TARGET_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_target_addr)],
        CONFIRM_SWAP: [CallbackQueryHandler(confirm_swap_order, pattern="^confirm_swap_order$")],
        WAITING_DEPOSIT_HASH: [
            CallbackQueryHandler(prompt_input_tx_hash, pattern="^input_swap_tx_"),
            MessageHandler(filters.TEXT | filters.PHOTO & ~filters.COMMAND, input_deposit_hash),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(cancel_swap, pattern="^cancel_swap$"),
        CallbackQueryHandler(cancel_swap, pattern="^cancel_swap_order_")
    ]
)
