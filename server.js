const { default: makeWASocket, useMultiFileAuthState } = require('@whiskeysockets/baileys');
const express = require('express');
const app = express();
app.use(express.json());

app.post('/get-pairing-code', async (req, res) => {
    const { phone } = req.body;
    if (!phone) return res.status(400).json({ error: 'Phone number is required' });

    try {
        // إنشاء جلسة مؤقتة برقم الهاتف المستهدف
        const { state, saveCreds } = await useMultiFileAuthState(`session_${phone.replace(/[^0-9]/g, '')}`);
        const sock = makeWASocket({
            auth: state,
            printQRInTerminal: false
        });

        // طلب كود الربط من سيرفرات واتساب الرسمية
        if (!sock.authState.creds.registered) {
            await new Promise(resolve => setTimeout(resolve, 3000)); // انتظار تهيئة الاتصال
            const code = await sock.requestPairingCode(phone.replace(/[^0-9]/g, ''));
            return res.json({ code: code });
        } else {
            return res.json({ error: 'الحساب مرتبط بالفعل!' });
        }
    } catch (err) {
        return res.status(500).json({ error: err.message });
    }
});

// تشغيل السيرفر المحلي على منفذ 3000
app.listen(3000, () => console.log('WA Service Connected on port 3000'));

