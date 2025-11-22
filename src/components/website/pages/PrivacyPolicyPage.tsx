import { Card } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'

interface PrivacyPolicyPageProps {
  navigate: (path: string) => void
}

export function PrivacyPolicyPage({ navigate }: PrivacyPolicyPageProps) {
  return (
    <div className="pt-16">
      <section className="py-12 bg-gradient-to-br from-primary/5 via-background to-accent/10">
        <div className="max-w-4xl mx-auto px-4 md:px-8">
          <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-4">
            Privacy Policy
          </h1>
          <p className="text-muted-foreground">
            Last Updated: {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
          </p>
        </div>
      </section>

      <section className="py-12">
        <div className="max-w-4xl mx-auto px-4 md:px-8">
          <Card className="p-8 md:p-12 bg-card">
            <div className="prose prose-slate max-w-none">
              <h2 className="text-2xl font-bold text-foreground mb-4">1. Introduction</h2>
              <p className="text-muted-foreground mb-6">
                Bitflow Nova ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you engage our digital services, visit our website, or communicate with us regarding custom digital solutions, software development, and related professional services.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">2. Information We Collect</h2>
              <p className="text-muted-foreground mb-4">
                We collect information that you provide directly to us, including:
              </p>
              <ul className="list-disc pl-6 text-muted-foreground space-y-2 mb-6">
                <li><strong>Contact Information:</strong> Name, email address, phone number, and company details when you request consultations or quotes</li>
                <li><strong>Project Information:</strong> Details about your business needs, technical requirements, and project specifications</li>
                <li><strong>Communication Records:</strong> Correspondence, support requests, and feedback you provide</li>
                <li><strong>Usage Data:</strong> Information about how you interact with our website and services</li>
                <li><strong>Technical Data:</strong> IP address, browser type, device information, and cookies</li>
              </ul>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">3. How We Use Your Information</h2>
              <p className="text-muted-foreground mb-4">
                We use the information we collect to:
              </p>
              <ul className="list-disc pl-6 text-muted-foreground space-y-2 mb-6">
                <li>Provide, maintain, and improve our digital services and custom solutions</li>
                <li>Respond to your inquiries, provide quotes, and deliver consultation services</li>
                <li>Communicate with you about projects, updates, and service-related information</li>
                <li>Process and complete transactions and send related information</li>
                <li>Monitor and analyze usage patterns to improve our services</li>
                <li>Protect against fraudulent, unauthorized, or illegal activity</li>
                <li>Comply with legal obligations and enforce our terms</li>
              </ul>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">4. Information Sharing and Disclosure</h2>
              <p className="text-muted-foreground mb-6">
                We do not sell or rent your personal information to third parties. We may share your information only in the following circumstances:
              </p>
              <ul className="list-disc pl-6 text-muted-foreground space-y-2 mb-6">
                <li><strong>Service Providers:</strong> With trusted third-party vendors who assist in operating our business (e.g., hosting providers, analytics services)</li>
                <li><strong>Legal Requirements:</strong> When required by law, court order, or governmental regulation</li>
                <li><strong>Business Transfers:</strong> In connection with a merger, acquisition, or sale of assets</li>
                <li><strong>With Your Consent:</strong> When you explicitly authorize us to share specific information</li>
              </ul>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">5. Data Security</h2>
              <p className="text-muted-foreground mb-6">
                We implement industry-standard security measures to protect your information from unauthorized access, alteration, disclosure, or destruction. These measures include encryption, secure server infrastructure, access controls, and regular security audits. However, no method of transmission over the internet is 100% secure, and we cannot guarantee absolute security.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">6. Data Retention</h2>
              <p className="text-muted-foreground mb-6">
                We retain your personal information for as long as necessary to fulfill the purposes outlined in this Privacy Policy, unless a longer retention period is required or permitted by law. Project-related data may be retained for the duration of the engagement and for a reasonable period thereafter for support and legal compliance purposes.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">7. Your Rights and Choices</h2>
              <p className="text-muted-foreground mb-4">
                You have the following rights regarding your personal information:
              </p>
              <ul className="list-disc pl-6 text-muted-foreground space-y-2 mb-6">
                <li><strong>Access:</strong> Request access to the personal information we hold about you</li>
                <li><strong>Correction:</strong> Request correction of inaccurate or incomplete information</li>
                <li><strong>Deletion:</strong> Request deletion of your personal information, subject to legal obligations</li>
                <li><strong>Objection:</strong> Object to processing of your information for certain purposes</li>
                <li><strong>Portability:</strong> Request a copy of your information in a structured format</li>
              </ul>
              <p className="text-muted-foreground mb-6">
                To exercise these rights, please contact us at bitflownova@gmail.com.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">8. Cookies and Tracking Technologies</h2>
              <p className="text-muted-foreground mb-6">
                We use cookies and similar tracking technologies to collect usage information and improve your experience. You can control cookies through your browser settings, though disabling cookies may affect website functionality.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">9. Third-Party Links</h2>
              <p className="text-muted-foreground mb-6">
                Our website may contain links to third-party websites. We are not responsible for the privacy practices of these external sites and encourage you to review their privacy policies.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">10. Children's Privacy</h2>
              <p className="text-muted-foreground mb-6">
                Our services are not directed to individuals under the age of 18. We do not knowingly collect personal information from children. If we become aware that we have collected information from a child, we will take steps to delete it promptly.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">11. International Data Transfers</h2>
              <p className="text-muted-foreground mb-6">
                Your information may be transferred to and processed in countries other than your country of residence. We ensure appropriate safeguards are in place to protect your information in accordance with this Privacy Policy.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">12. Changes to This Privacy Policy</h2>
              <p className="text-muted-foreground mb-6">
                We may update this Privacy Policy from time to time. We will notify you of any material changes by posting the new policy on this page and updating the "Last Updated" date. Your continued use of our services after such modifications constitutes acceptance of the updated policy.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">13. Contact Us</h2>
              <p className="text-muted-foreground mb-4">
                If you have questions or concerns about this Privacy Policy or our data practices, please contact us:
              </p>
              <div className="bg-muted/50 p-6 rounded-lg">
                <p className="text-foreground font-semibold mb-2">Bitflow Nova</p>
                <p className="text-muted-foreground">Email: bitflownova@gmail.com</p>
              </div>
            </div>
          </Card>
        </div>
      </section>
    </div>
  )
}
