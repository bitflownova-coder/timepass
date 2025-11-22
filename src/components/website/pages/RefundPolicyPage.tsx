import { Card } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'

interface RefundPolicyPageProps {
  navigate: (path: string) => void
}

export function RefundPolicyPage({ navigate }: RefundPolicyPageProps) {
  return (
    <div className="pt-16">
      <section className="py-12 bg-gradient-to-br from-primary/5 via-background to-accent/10">
        <div className="max-w-4xl mx-auto px-4 md:px-8">
          <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-4">
            Refund Policy
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
              <h2 className="text-2xl font-bold text-foreground mb-4">1. Policy Overview</h2>
              <p className="text-muted-foreground mb-6">
                At Bitflow Nova, we are committed to delivering exceptional digital solutions with Fast Turnaround and Unmatched Support. This Refund Policy outlines the conditions under which refunds may be requested for our custom digital service contracts, including AI Development, Cyber Security, Software Development, Automation Tools, App Development, Digital Marketing, Web Development, CMS Development, and SEO services. Because our services involve custom development work tailored to each client's specific needs, refund eligibility is limited to specific circumstances outlined below.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">2. Custom Service Nature</h2>
              <p className="text-muted-foreground mb-6">
                All services provided by Bitflow Nova are custom digital solutions designed and developed specifically for each client's unique requirements. Work begins immediately upon project commencement, and resources are allocated based on the agreed Statement of Work (SOW) or project agreement. Due to the bespoke nature of our services, standard consumer refund policies do not apply. Refunds are evaluated on a case-by-case basis according to the specific circumstances and project phase.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">3. Refund Eligibility</h2>
              <p className="text-muted-foreground mb-4">
                Refund requests may be considered in the following limited circumstances:
              </p>
              
              <h3 className="text-xl font-semibold text-foreground mb-3 mt-6">3.1 Non-Commencement of Work</h3>
              <p className="text-muted-foreground mb-6">
                If Bitflow Nova has not commenced substantive work on the project within 7 business days of receiving the initial deposit and all required client materials, clients may request a full refund of payments made. "Substantive work" includes requirements gathering, design planning, architecture development, or any deliverable production.
              </p>

              <h3 className="text-xl font-semibold text-foreground mb-3">3.2 Failure to Meet Agreed Specifications</h3>
              <p className="text-muted-foreground mb-6">
                If final deliverables materially fail to meet the specifications outlined in the agreed SOW or contract, and we are unable to remedy such deficiencies within 15 business days of written notification, clients may be eligible for a partial refund. The refund amount will be proportional to the portion of deliverables that do not meet specifications, as determined through good-faith negotiation or, if necessary, independent technical evaluation.
              </p>

              <h3 className="text-xl font-semibold text-foreground mb-3">3.3 Project Cancellation by Bitflow Nova</h3>
              <p className="text-muted-foreground mb-6">
                In the unlikely event that Bitflow Nova must cancel a project due to unforeseen circumstances preventing completion (excluding client-caused delays or force majeure), clients will receive a full refund of any payments made for work not completed, less the value of any work products already delivered and accepted.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">4. Non-Refundable Circumstances</h2>
              <p className="text-muted-foreground mb-4">
                Refunds will NOT be provided in the following circumstances:
              </p>
              <ul className="list-disc pl-6 text-muted-foreground space-y-2 mb-6">
                <li><strong>Change of Mind:</strong> Client decides they no longer want or need the services after work has commenced</li>
                <li><strong>Subjective Preferences:</strong> Client dislikes aesthetic choices, design styles, or implementation approaches that were not specified in the original agreement</li>
                <li><strong>Client-Caused Delays:</strong> Project delays or complications resulting from client failure to provide required materials, feedback, or approvals</li>
                <li><strong>Completed Work:</strong> Services that have been completed and delivered according to agreed specifications</li>
                <li><strong>Partial Delivery:</strong> Phases or milestones that have been completed and accepted, even if the full project is not complete</li>
                <li><strong>Third-Party Dependencies:</strong> Issues arising from third-party services, platforms, or integrations outside our control</li>
                <li><strong>Post-Delivery Issues:</strong> Problems arising from client modifications, hosting environment issues, or improper use of deliverables after delivery and acceptance</li>
                <li><strong>Market Performance:</strong> SEO rankings, marketing campaign results, or business outcomes that depend on market factors beyond our control</li>
                <li><strong>Discovery/Consultation Services:</strong> Time spent on consultations, strategy sessions, discovery phases, or planning once these services have been rendered</li>
              </ul>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">5. Refund Request Process</h2>
              <p className="text-muted-foreground mb-4">
                To request a refund, clients must:
              </p>
              <ol className="list-decimal pl-6 text-muted-foreground space-y-3 mb-6">
                <li>Submit a written refund request to bitflownova@gmail.com within 30 days of the circumstance giving rise to the request</li>
                <li>Provide a detailed explanation of the grounds for the refund request, including specific references to agreed specifications or contract terms</li>
                <li>Include supporting documentation, communications, or evidence relevant to the request</li>
                <li>Allow Bitflow Nova 10 business days to review the request and respond</li>
                <li>Engage in good-faith dialogue to resolve any disputes before pursuing formal dispute resolution</li>
              </ol>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">6. Refund Evaluation and Timeline</h2>
              <p className="text-muted-foreground mb-6">
                Upon receiving a refund request, we will conduct a thorough review of the project, including examination of all deliverables, communications, and agreed specifications. We will respond to refund requests within 10 business days with either: (a) approval of the refund with the amount and timeline; (b) a proposed alternative resolution, such as additional revisions or modifications; or (c) a detailed explanation if the request is denied. Approved refunds will be processed within 15 business days using the original payment method.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">7. Partial Refunds</h2>
              <p className="text-muted-foreground mb-6">
                When projects are partially completed or certain milestones have been delivered and accepted, refunds will be calculated on a pro-rata basis. The refund amount will reflect: (a) total fees paid; (b) minus the value of completed and delivered work; (c) minus any non-recoverable costs incurred (such as third-party licenses or services purchased specifically for the project). All partial refund calculations will be documented and explained to the client.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">8. Satisfaction Guarantee Alternative</h2>
              <p className="text-muted-foreground mb-6">
                In lieu of refunds, Bitflow Nova prioritizes client satisfaction through our commitment to Unmatched Support and quality work. Before requesting a refund, we strongly encourage clients to work with us on resolving any concerns. We offer: (a) reasonable revisions to deliverables within scope; (b) clarification and technical support; (c) collaborative problem-solving to address any issues; and (d) project adjustments when feasible. Our goal is always to deliver solutions that meet your needs rather than process refunds.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">9. Deposit and Payment Structure</h2>
              <p className="text-muted-foreground mb-6">
                Our standard payment structure requires a 50% deposit upon project commencement. This deposit secures resources, initiates planning and development work, and may cover third-party costs. Deposits are non-refundable once work has commenced, except in the specific circumstances outlined in Section 3 above. The remaining 50% payment is due upon project completion and is subject to this refund policy only if deliverables materially fail to meet agreed specifications.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">10. Chargebacks and Payment Disputes</h2>
              <p className="text-muted-foreground mb-6">
                Initiating a chargeback or payment dispute without first following the refund request process outlined above constitutes a breach of the service agreement. Chargebacks for delivered services may result in: (a) immediate suspension of all services; (b) revocation of licenses for delivered work products; (c) pursuit of payment through collections or legal action; and (d) termination of the client relationship. We strongly encourage clients to work directly with us to resolve any payment concerns.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">11. Force Majeure</h2>
              <p className="text-muted-foreground mb-6">
                Refunds are not provided for delays or non-performance caused by circumstances beyond our reasonable control, including but not limited to: natural disasters, pandemics, government actions, internet service disruptions, third-party platform outages, or other force majeure events. In such cases, project timelines will be reasonably extended, and we will work collaboratively with clients to minimize impact.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">12. Modifications to This Policy</h2>
              <p className="text-muted-foreground mb-6">
                Bitflow Nova reserves the right to modify this Refund Policy at any time. Changes will be effective immediately upon posting to our website. The version of this policy in effect at the time of contract execution governs that specific engagement. Continued engagement with our services after policy changes constitutes acceptance of the modified terms.
              </p>

              <Separator className="my-8" />

              <h2 className="text-2xl font-bold text-foreground mb-4">13. Contact Information</h2>
              <p className="text-muted-foreground mb-4">
                For refund requests or questions about this policy, please contact:
              </p>
              <div className="bg-muted/50 p-6 rounded-lg">
                <p className="text-foreground font-semibold mb-2">Bitflow Nova</p>
                <p className="text-muted-foreground">Email: bitflownova@gmail.com</p>
                <p className="text-muted-foreground mt-4 text-sm">
                  Please include "Refund Request" in your email subject line and provide your project details and account information.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </section>
    </div>
  )
}
