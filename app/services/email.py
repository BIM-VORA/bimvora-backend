"""Transactional emails via Resend."""
import logging

import resend

from app.config import settings

logger = logging.getLogger("bimvora.email")

resend.api_key = settings.resend_api_key


async def send_order_confirmation_email(order, download_tokens: list[dict]) -> None:
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not set — skipping email")
        return

    frontend_url = settings.frontend_url
    items_html = ""
    for item in download_tokens:
        download_url = f"{frontend_url}/downloads?token={item['token']}"
        items_html += f"""
        <div style="margin-bottom:16px;padding:20px;background:#F7F9FC;border-radius:8px;border:1px solid #DDE3EE;">
            <p style="margin:0 0 4px;font-weight:600;font-size:15px;">{item['product_name']}</p>
            <p style="margin:0 0 12px;color:#6B7280;font-size:13px;">{item['file_name']} · {item['file_size_mb']} MB</p>
            <a href="{download_url}" style="display:inline-block;padding:10px 20px;background:#0047CC;color:white;border-radius:6px;text-decoration:none;font-weight:600;font-size:14px;">
                ⬇ Download Now
            </a>
        </div>
        """

    total_usd = order.total_cents / 100

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:Inter,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:40px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:12px;overflow:hidden;">
        
        <!-- Header -->
        <tr><td style="background:#0A0E1A;padding:28px 40px;text-align:center;">
          <span style="color:#ffffff;font-size:22px;font-weight:700;letter-spacing:0.15em;">BIMVORA</span>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:40px;">
          <h1 style="margin:0 0 8px;font-size:22px;color:#0A0E1A;">Your Revit families are ready ✅</h1>
          <p style="margin:0 0 24px;color:#6B7280;font-size:15px;">Hello {order.customer_first_name}, your payment has been confirmed.</p>

          <div style="background:#F0FFF4;border:1px solid #BBF7D0;border-radius:8px;padding:16px 20px;margin-bottom:28px;">
            <table width="100%"><tr>
              <td style="font-size:13px;color:#166534;">Order <strong>#{order.order_number}</strong></td>
              <td style="text-align:right;font-size:13px;color:#166534;font-weight:700;">${total_usd:.2f} {order.currency}</td>
            </tr></table>
          </div>

          <h2 style="font-size:16px;font-weight:600;border-bottom:1px solid #DDE3EE;padding-bottom:12px;margin:0 0 20px;">Your Downloads</h2>
          {items_html}

          <div style="background:#FFF7ED;border-radius:8px;padding:20px;margin-top:28px;">
            <p style="margin:0 0 12px;font-weight:600;font-size:14px;color:#9A3412;">⚡ How to use your Revit family</p>
            <ol style="margin:0;padding-left:18px;color:#78350F;font-size:13px;line-height:1.8;">
              <li>Open Revit → Insert → Load Family</li>
              <li>Select the downloaded <code>.rfa</code> file</li>
              <li>Place the family in your project</li>
              <li>Connect to your MEP system</li>
              <li>Schedule from shared parameters</li>
            </ol>
          </div>

          <p style="margin:28px 0 0;font-size:13px;color:#6B7280;">
            Download links expire in 1 year. Access them anytime at 
            <a href="{frontend_url}/account/downloads" style="color:#0047CC;">your account page</a>.
          </p>
        </td></tr>

        <!-- Footer -->
        <tr><td style="background:#F7F9FC;padding:20px 40px;text-align:center;border-top:1px solid #DDE3EE;">
          <p style="margin:0;font-size:12px;color:#9CA3AF;">
            BIMVORA · Professional BIM Content · 
            <a href="{frontend_url}" style="color:#0047CC;text-decoration:none;">bimvora.com</a>
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    resend.Emails.send({
        "from": f"BIMVORA <{settings.email_from}>",
        "to": [order.customer_email],
        "subject": f"Your BIMVORA order is ready — #{order.order_number}",
        "html": html,
        "reply_to": "support@bimvora.com",
    })
    logger.info(f"Confirmation email sent to {order.customer_email}")
