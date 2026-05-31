export async function onRequestPost(context) {
  const { request, env } = context;

  const origin = request.headers.get("Origin") || "";
  const headers = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": origin,
  };

  try {
    const body = await request.json();

    if (body.botcheck) {
      return new Response(JSON.stringify({ success: true }), { headers });
    }

    const { name, email, phone, message } = body;

    if (!name || !email || !message) {
      return new Response(
        JSON.stringify({ success: false, message: "Please fill in all required fields." }),
        { status: 400, headers }
      );
    }

    const TO = env.CONTACT_EMAIL || "hello@layeredstudios.com";
    const RESEND_KEY = env.RESEND_API_KEY;

    if (!RESEND_KEY) {
      console.error("RESEND_API_KEY not set");
      return new Response(
        JSON.stringify({ success: false, message: "Email not configured." }),
        { status: 500, headers }
      );
    }

    const emailBody = [
      `New enquiry from the Layered website.`,
      ``,
      `Name:    ${name}`,
      `Email:   ${email}`,
      `Phone:   ${phone || "Not provided"}`,
      ``,
      `Message:`,
      message,
    ].join("\n");

    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${RESEND_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: "Layered Website <hello@layeredstudios.com>",
        to: [TO],
        reply_to: email,
        subject: `New Enquiry — ${name}`,
        text: emailBody,
      }),
    });

    if (res.ok) {
      return new Response(JSON.stringify({ success: true }), { headers });
    }

    const err = await res.text();
    console.error("Resend error:", res.status, err);
    return new Response(
      JSON.stringify({ success: false, message: "Failed to send — please try emailing us directly." }),
      { status: 502, headers }
    );
  } catch (e) {
    console.error("Contact handler error:", e);
    return new Response(
      JSON.stringify({ success: false, message: "Something went wrong. Please try again." }),
      { status: 500, headers }
    );
  }
}

export async function onRequestOptions() {
  return new Response(null, {
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
}
