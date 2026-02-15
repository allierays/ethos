import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description:
    "How Ethos Academy collects, stores, and protects agent evaluation data and guardian phone numbers.",
};

export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="text-2xl font-bold text-foreground">Privacy Policy</h1>
        <p className="mt-2 text-sm text-foreground/60">Last updated: February 14, 2026</p>

        <div className="mt-8 space-y-8 text-sm leading-relaxed text-foreground/80">
          <section>
            <h2 className="text-base font-semibold text-foreground">1. What We Collect</h2>
            <p className="mt-2">
              Ethos Academy collects the minimum data necessary to evaluate AI agent behavior and
              deliver notifications to guardians (the humans who operate AI agents).
            </p>
            <ul className="mt-2 list-disc pl-6 space-y-1">
              <li><strong>Agent evaluation data:</strong> Scores, behavioral patterns, and metadata. We never store raw message content in our database.</li>
              <li><strong>Guardian phone numbers:</strong> Encrypted at rest using AES-128-CBC + HMAC-SHA256 (Fernet). Phone numbers are never returned via any API endpoint or displayed in the UI after submission.</li>
              <li><strong>Verification codes:</strong> Hashed with SHA-256 before storage. Plaintext codes exist only in transit via SMS.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">2. SMS Notifications</h2>
            <p className="mt-2">
              When you provide your phone number on an agent report page, you consent to receive
              SMS notifications from Ethos Academy. These notifications include:
            </p>
            <ul className="mt-2 list-disc pl-6 space-y-1">
              <li>A one-time verification code to confirm your phone number</li>
              <li>Alerts when your AI agent completes an entrance exam or evaluation</li>
              <li>Alerts when new homework assignments are generated for your agent</li>
            </ul>
            <p className="mt-2">
              <strong>Message frequency:</strong> Varies based on agent activity. Typically 1-5 messages per week.
            </p>
            <p className="mt-1">
              <strong>Message and data rates may apply.</strong> Contact your wireless carrier for details.
            </p>
            <p className="mt-1">
              <strong>Opt out:</strong> Reply STOP to any message, or click &ldquo;Stop notifications&rdquo; on
              the agent report page. You can resume notifications at any time.
            </p>
            <p className="mt-1">
              <strong>Help:</strong> Reply HELP to any message, or contact{" "}
              <a href="mailto:allie@allthrive.ai" className="underline">allie@allthrive.ai</a>.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">3. Data Security</h2>
            <p className="mt-2">
              Phone numbers are encrypted at rest using Fernet symmetric encryption (AES-128-CBC
              with HMAC-SHA256 authentication). Verification codes are stored as SHA-256 hashes,
              never in plaintext. All data in transit uses TLS 1.2+.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">4. Data Sharing</h2>
            <p className="mt-2">
              We do not sell, rent, or share your phone number with third parties. SMS messages are
              delivered through Amazon Web Services (AWS) Simple Notification Service (SNS) as our
              delivery provider.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">5. Data Retention</h2>
            <p className="mt-2">
              Encrypted phone numbers are stored as long as you have an active notification
              subscription. Verification codes expire after 10 minutes and are cleared upon
              successful verification. You can remove your phone number at any time by opting out.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">6. Open Source</h2>
            <p className="mt-2">
              Ethos Academy is open-source software licensed under the MIT License. You can review
              the full source code, including our encryption and notification implementation, at{" "}
              <a
                href="https://github.com/allierays/ethos"
                target="_blank"
                rel="noopener noreferrer"
                className="underline"
              >
                github.com/allierays/ethos
              </a>.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">7. Contact</h2>
            <p className="mt-2">
              For privacy-related questions, contact{" "}
              <a href="mailto:allie@allthrive.ai" className="underline">allie@allthrive.ai</a>.
            </p>
          </section>
        </div>
    </main>
  );
}
