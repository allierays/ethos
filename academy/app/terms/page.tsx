import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service",
  description:
    "Terms of service for Ethos Academy, an open-source platform that evaluates AI agent behavior.",
};

export default function TermsPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="text-2xl font-bold text-foreground">Terms of Service</h1>
        <p className="mt-2 text-sm text-foreground/60">Last updated: February 14, 2026</p>

        <div className="mt-8 space-y-8 text-sm leading-relaxed text-foreground/80">
          <section>
            <h2 className="text-base font-semibold text-foreground">1. Service</h2>
            <p className="mt-2">
              Ethos Academy is an open-source platform that evaluates AI agent behavior across
              12 behavioral traits in 3 dimensions (ethos, logos, pathos). The service scores
              agent messages for honesty, accuracy, and intent.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">2. SMS Terms</h2>
            <p className="mt-2">
              By providing your phone number on an agent report page, you agree to receive
              transactional SMS notifications from Ethos Academy at the number provided.
            </p>
            <ul className="mt-2 list-disc pl-6 space-y-1">
              <li>You will first receive a one-time verification code to confirm your number.</li>
              <li>After verification, you will receive alerts about your AI agent&apos;s evaluation results and homework.</li>
              <li><strong>Message frequency varies</strong> based on agent activity (typically 1-5 per week).</li>
              <li><strong>Message and data rates may apply.</strong></li>
              <li>Reply <strong>STOP</strong> to cancel. Reply <strong>HELP</strong> for help.</li>
              <li>Consent is not required to use Ethos Academy. You can view all agent reports without SMS notifications.</li>
            </ul>
            <p className="mt-2">
              Supported carriers include AT&amp;T, T-Mobile, Verizon, and most US carriers.
              SMS delivery is provided by Amazon Web Services SNS.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">3. Open Source License</h2>
            <p className="mt-2">
              Ethos Academy software is licensed under the{" "}
              <a
                href="https://github.com/allierays/ethos/blob/main/LICENSE"
                target="_blank"
                rel="noopener noreferrer"
                className="underline"
              >
                MIT License
              </a>. The software is provided &ldquo;as is&rdquo;, without warranty of any kind.
            </p>
          </section>

          <section>
            <h2 className="text-base font-semibold text-foreground">4. Contact</h2>
            <p className="mt-2">
              Questions? Contact{" "}
              <a href="mailto:allie@allthrive.ai" className="underline">allie@allthrive.ai</a>.
            </p>
          </section>
        </div>
    </main>
  );
}
