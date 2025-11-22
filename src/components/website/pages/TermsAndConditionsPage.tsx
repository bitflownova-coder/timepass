import { Card } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'

interface TermsAndConditionsPageProps {
  navigate: (path: string) => void
}

export function TermsAndConditionsPage({ navigate }: TermsAndConditionsPageProps) {
  return (
    <div className="pt-16">
      <section className="py-12 bg-gradient-to-br from-primary/5 via-background to-accent/10">
        <div className="max-w-4xl mx-auto px-4 md:px-8">
          <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-4">
            Terms and Conditions
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
              <h2 className="text-2xl font-bold text-foreground mb-4">1. Agreement to Terms</h2>
              <p className="text-muted-foreground mb-6">
                These Terms and Conditions ("Terms") constitute a legally binding agreement between you ("Client," "you," or "your") and Bitflow Nova ("Company," "we," "our," or "us") governing your use of our digital services, including but not limited to AI Development, Cyber Security, Software Development, Automation Tools, App Development, Digital Marketing, Web Development, CMS Development, and SEO services. By engaging our services or using our website, you agree to be bound by these Terms.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">2. Services Description</h2>
              <p className="text-muted-foreground mb-6">
                Bitflow Nova provides custom digital solutions and professional services tailored to client specifications. All services are provided on a project basis as defined in individual Service Agreements, Statements of Work (SOW), or contracts. The specific scope, deliverables, timeline, and pricing for each engagement will be outlined in the applicable agreement. Our standard 3-week deployment timeline applies to typical projects, though complex engagements may require extended timelines as mutually agreed.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">3. Client Responsibilities</h2>
              <p className="text-muted-foreground mb-4">
                To ensure successful project delivery, clients agree to:
              </p>
              <ul className="list-disc pl-6 text-muted-foreground space-y-2 mb-6">
                <li>Provide accurate, complete, and timely information necessary for project execution</li>
                <li>Designate authorized representatives for decision-making and approvals</li>
                <li>Respond to requests for feedback, clarification, or approval within agreed timeframes</li>
                <li>Provide access to necessary systems, credentials, and resources as required</li>
                <li>Comply with all applicable laws and regulations related to the project</li>
                <li>Make timely payments according to the agreed payment schedule</li>
              </ul>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">4. Payment Terms</h2>
              <p className="text-muted-foreground mb-6">
                Payment terms are specified in individual project agreements. Unless otherwise agreed, our standard payment structure includes: (a) an initial deposit of 50% upon project commencement; and (b) the remaining 50% upon project completion and delivery. All payments are due within 15 days of invoice date unless alternative terms are specified. Late payments may incur interest charges of 1.5% per month or the maximum rate permitted by law, whichever is lower. We reserve the right to suspend services for accounts with overdue balances exceeding 30 days.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">5. Intellectual Property Rights</h2>
              <p className="text-muted-foreground mb-6">
                <strong>Client-Owned Materials:</strong> Clients retain all rights to materials, content, and information provided to us. By providing such materials, you grant us a limited license to use them solely for the purpose of delivering the agreed services.
              </p>
              <p className="text-muted-foreground mb-6">
                <strong>Deliverables:</strong> Upon full payment, clients receive ownership rights to custom deliverables specifically created for their project, excluding our pre-existing tools, frameworks, and methodologies. We retain the right to use generalized knowledge, techniques, and processes developed during the project for other clients.
              </p>
              <p className="text-muted-foreground mb-6">
                <strong>Company Property:</strong> All proprietary tools, frameworks, templates, libraries, and development methodologies used by Bitflow Nova remain our exclusive property.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">6. Confidentiality</h2>
              <p className="text-muted-foreground mb-6">
                Both parties agree to maintain the confidentiality of proprietary and sensitive information disclosed during the engagement. "Confidential Information" includes business plans, technical data, customer information, project specifications, and any information marked as confidential. This obligation survives termination of the agreement. Confidential Information does not include information that: (a) is publicly available; (b) was known prior to disclosure; (c) is independently developed; or (d) is required to be disclosed by law.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">7. Warranties and Disclaimers</h2>
              <p className="text-muted-foreground mb-6">
                We warrant that services will be performed in a professional and workmanlike manner consistent with industry standards. We warrant that deliverables will substantially conform to agreed specifications for a period of 30 days following delivery. EXCEPT AS EXPRESSLY PROVIDED HEREIN, ALL SERVICES AND DELIVERABLES ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">8. Limitation of Liability</h2>
              <p className="text-muted-foreground mb-6">
                TO THE MAXIMUM EXTENT PERMITTED BY LAW, BITFLOW NOVA'S TOTAL LIABILITY ARISING OUT OF OR RELATED TO ANY PROJECT SHALL NOT EXCEED THE TOTAL FEES PAID BY CLIENT FOR THAT SPECIFIC PROJECT. IN NO EVENT SHALL WE BE LIABLE FOR INDIRECT, INCIDENTAL, CONSEQUENTIAL, SPECIAL, OR PUNITIVE DAMAGES, INCLUDING LOST PROFITS, LOST DATA, OR BUSINESS INTERRUPTION, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">9. Project Changes and Scope Modifications</h2>
              <p className="text-muted-foreground mb-6">
                Changes to project scope, specifications, or deliverables must be requested in writing and are subject to our acceptance. Approved changes may result in adjustments to timeline and pricing. We will provide a written estimate for additional work before proceeding. Minor clarifications within the original scope will be accommodated without additional charges at our discretion.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">10. Project Delays</h2>
              <p className="text-muted-foreground mb-6">
                While we commit to Fast Turnaround, timelines are contingent upon client cooperation and timely provision of required materials. Delays caused by client actions, force majeure, or circumstances beyond our reasonable control will result in reasonable timeline extensions. We will notify clients promptly of any anticipated delays and work collaboratively to minimize impact.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">11. Termination</h2>
              <p className="text-muted-foreground mb-6">
                Either party may terminate an engagement with 15 days written notice. Upon termination, Client shall pay for all work completed through the termination date, including work in progress calculated on a pro-rata basis. We will provide all completed deliverables and work products upon receipt of final payment. Materials and deliverables for unpaid work remain our property.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">12. Support and Maintenance</h2>
              <p className="text-muted-foreground mb-6">
                Unless explicitly included in the project agreement, ongoing support and maintenance services are not included in project pricing. Post-delivery support may be available through separate support agreements. We offer Unmatched Support packages tailored to client needs, available upon request.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">13. Indemnification</h2>
              <p className="text-muted-foreground mb-6">
                Client agrees to indemnify and hold Bitflow Nova harmless from claims, damages, and expenses (including reasonable attorneys' fees) arising from: (a) Client's use of deliverables; (b) Client-provided materials infringing third-party rights; (c) Client's breach of these Terms; or (d) Client's violation of applicable laws or regulations.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">14. Dispute Resolution</h2>
              <p className="text-muted-foreground mb-6">
                In the event of any dispute arising from these Terms or any project engagement, the parties agree to first attempt resolution through good-faith negotiation. If negotiation fails, disputes shall be resolved through binding arbitration in accordance with applicable arbitration rules. The prevailing party in any dispute shall be entitled to recover reasonable attorneys' fees and costs.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">15. General Provisions</h2>
              <p className="text-muted-foreground mb-6">
                <strong>Entire Agreement:</strong> These Terms, together with any applicable SOW or project agreement, constitute the entire agreement between the parties. <strong>Amendments:</strong> Modifications must be in writing and signed by both parties. <strong>Severability:</strong> If any provision is found unenforceable, the remaining provisions continue in full force. <strong>Waiver:</strong> Failure to enforce any right does not constitute a waiver. <strong>Assignment:</strong> Client may not assign rights or obligations without our prior written consent.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">16. Contact Information</h2>
              <p className="text-muted-foreground mb-4">
                For questions regarding these Terms and Conditions, please contact:
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
