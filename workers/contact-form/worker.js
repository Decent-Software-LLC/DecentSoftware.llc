const ALLOWED_ORIGINS = new Set([
  "https://decentsoftware.llc",
  "https://www.decentsoftware.llc",
  "https://dev.decentsoftware.llc",
  "https://decentsoftware-llc-dev.pages.dev",
]);

const RECIPIENTS = [
  "donniegardner3rd@gmail.com",
  "kevin.d.jones@gmail.com",
];

const MAX_BODY_BYTES = 16_384;

function response(origin, status, payload) {
  const headers = {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
  };

  if (ALLOWED_ORIGINS.has(origin)) {
    headers["Access-Control-Allow-Origin"] = origin;
    headers["Access-Control-Allow-Headers"] = "Content-Type";
    headers["Access-Control-Allow-Methods"] = "POST, OPTIONS";
    headers.Vary = "Origin";
  }

  return new Response(status === 204 ? null : JSON.stringify(payload), { status, headers });
}

function cleanSingleLine(value, maxLength) {
  if (typeof value !== "string") return "";
  return value
    .normalize("NFKC")
    .replace(/[\u0000-\u001f\u007f]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, maxLength);
}

function cleanComments(value) {
  if (typeof value !== "string") return "";
  return value
    .normalize("NFKC")
    .replace(/\r\n?/g, "\n")
    .replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g, "")
    .trim()
    .slice(0, 3000);
}

function validate(payload) {
  const name = cleanSingleLine(payload.name, 80);
  const email = cleanSingleLine(payload.email, 254).toLowerCase();
  const phone = cleanSingleLine(payload.phone, 32);
  const comments = cleanComments(payload.comments);
  const company = cleanSingleLine(payload.company, 100);

  if (company) return { spam: true };

  if (!/^[\p{L}\p{M} .'-]{2,80}$/u.test(name)) {
    return { error: "Please enter a valid name." };
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/u.test(email)) {
    return { error: "Please enter a valid email address." };
  }

  if (!/^[+0-9().\- xX]{7,32}$/.test(phone)) {
    return { error: "Please enter a valid phone number." };
  }

  if (comments.length < 10 || comments.length > 3000) {
    return { error: "Comments must be between 10 and 3,000 characters." };
  }

  return { name, email, phone, comments };
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";

    if (!ALLOWED_ORIGINS.has(origin)) {
      return response(origin, 403, { error: "Origin not allowed." });
    }

    if (request.method === "OPTIONS") {
      return response(origin, 204, {});
    }

    if (request.method !== "POST") {
      return response(origin, 405, { error: "Method not allowed." });
    }

    if (!request.headers.get("Content-Type")?.toLowerCase().startsWith("application/json")) {
      return response(origin, 415, { error: "Content type must be application/json." });
    }

    const declaredLength = Number(request.headers.get("Content-Length") || 0);
    if (declaredLength > MAX_BODY_BYTES) {
      return response(origin, 413, { error: "Request is too large." });
    }

    const rateKey = `${request.headers.get("CF-Connecting-IP") || "unknown"}:contact`;
    if (env.CONTACT_LIMITER) {
      const { success } = await env.CONTACT_LIMITER.limit({ key: rateKey });
      if (!success) {
        return response(origin, 429, { error: "Too many messages. Please try again in a minute." });
      }
    }

    let payload;
    try {
      const rawBody = await request.text();
      if (new TextEncoder().encode(rawBody).byteLength > MAX_BODY_BYTES) {
        return response(origin, 413, { error: "Request is too large." });
      }
      payload = JSON.parse(rawBody);
    } catch {
      return response(origin, 400, { error: "Invalid request." });
    }

    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      return response(origin, 400, { error: "Invalid request." });
    }

    const form = validate(payload);
    if (form.spam) return response(origin, 200, { success: true });
    if (form.error) return response(origin, 400, { error: form.error });

    const submittedAt = new Date().toISOString();
    const subject = "New DecentSoftware.llc contact form submission";
    const text = [
      "New message from DecentSoftware.llc",
      "",
      `Name: ${form.name}`,
      `Email: ${form.email}`,
      `Phone: ${form.phone}`,
      `Submitted: ${submittedAt}`,
      "",
      "Comments:",
      form.comments,
    ].join("\n");
    const rawEmail = (recipient) => [
      "From: Decent Software Website <contact@decentsoftware.llc>",
      `To: ${recipient}`,
      `Reply-To: ${form.name} <${form.email}>`,
      `Subject: ${subject}`,
      "MIME-Version: 1.0",
      "Content-Type: text/plain; charset=UTF-8",
      "Content-Transfer-Encoding: 8bit",
      "",
      text,
    ].join("\r\n");

    try {
      await Promise.all(RECIPIENTS.map((recipient) => env.EMAIL.send(
        new EmailMessage(
          "contact@decentsoftware.llc",
          recipient,
          rawEmail(recipient),
        ),
      )));
      return response(origin, 200, { success: true });
    } catch (error) {
      console.error("Contact email failed", error?.code || "unknown", error?.message || error);
      return response(origin, 503, { error: "We couldn’t send your message. Please try again shortly." });
    }
  },
};
import { EmailMessage } from "cloudflare:email";
