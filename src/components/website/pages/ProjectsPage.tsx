import { Card } from '@/components/ui/card'
import { ArrowRight, ArrowUpRight } from '@phosphor-icons/react'

interface ProjectsPageProps {
  navigate: (path: string) => void
}

const projects = [
  {
    title: 'Sage Helix 360',
    industry: 'Education',
    year: '2024',
    description: 'Comprehensive EdTech platform transformation integrating modern web technologies and CMS capabilities. Leveraged AI Development to create personalized learning pathways that adapt to individual student needs and performance metrics. The solution seamlessly combines content delivery, student engagement tools, and advanced analytics to drive educational outcomes. Our Expert Professionals delivered a scalable architecture supporting thousands of concurrent users while maintaining exceptional performance. The platform includes interactive assessment tools, real-time progress tracking, and intelligent content recommendations powered by machine learning algorithms.',
    url: 'https://sage-edu.in/',
    services: ['Web Development', 'CMS Integration', 'AI Development', 'Cloud Infrastructure'],
    highlights: [
      'Personalized AI-driven learning pathways',
      'Scalable architecture for 10,000+ concurrent users',
      'Integrated analytics dashboard',
      'Fast Turnaround: Delivered in 3 weeks'
    ]
  },
  {
    title: 'APPICON 2024',
    industry: 'Healthcare',
    year: '2024',
    description: 'Large-scale medical conference platform featuring automated registration workflows and comprehensive attendee management. Built custom App Development solutions to streamline check-in processes and real-time session tracking. Integrated Digital Marketing automation to drive registration conversions and engagement. The platform successfully handled complex multi-track scheduling while ensuring data security compliance for sensitive healthcare professional information, showcasing our Unmatched Support throughout the event lifecycle. Advanced features included QR code-based attendance tracking, live session updates, and automated certificate generation for participants.',
    url: 'https://www.appicon2024chennai.com/',
    services: ['App Development', 'Digital Marketing', 'Automation', 'Security'],
    highlights: [
      'Automated multi-track conference management',
      'QR code attendance and check-in system',
      'Unmatched Support: 24/7 technical assistance',
      'Processed 5,000+ registrations seamlessly'
    ]
  },
  {
    title: 'Forensic Medicon 2025',
    industry: 'Healthcare / Enterprise',
    year: '2025',
    description: 'Mission-critical conference platform deployed with enterprise-grade Cyber Security infrastructure protecting sensitive forensic data. Delivered comprehensive Web Development solution with robust authentication and encrypted data transmission. The project exemplifies our Fast Turnaround capability, completed from requirements to production in just 3 weeks without compromising security standards. Built scalable cloud infrastructure supporting peak load during registration periods while maintaining HIPAA compliance for healthcare data handling. Implementation included advanced threat detection, multi-factor authentication, and encrypted database storage for sensitive forensic case information.',
    url: 'https://www.forensicmedicon2025chennai.com/',
    services: ['Cyber Security', 'Web Development', 'Cloud Infrastructure', 'Compliance'],
    highlights: [
      'Enterprise-grade security with encryption',
      'HIPAA compliant data handling',
      'Fast Turnaround: 3-week deployment',
      'Multi-factor authentication system'
    ]
  }
]

export function ProjectsPage({ navigate }: ProjectsPageProps) {
  return (
    <div className="pt-16">
      <section className="py-20 bg-gradient-to-br from-primary/5 via-background to-accent/10">
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-4">
              Our Work in Action
            </h1>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Real-world results across Education, Healthcare, and Enterprise verticals demonstrating Expert Professionals delivering Fast Turnaround with Unmatched Support
            </p>
          </div>
        </div>
      </section>

      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <div className="space-y-16">
            {projects.map((project, index) => (
              <div key={project.title}>
                <Card className="overflow-hidden hover:shadow-2xl transition-shadow">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-0">
                    <div className={`p-8 lg:p-12 ${index % 2 === 0 ? 'lg:order-1' : 'lg:order-2'}`}>
                      <div className="flex items-center gap-3 mb-4">
                        <span className="text-sm font-semibold text-accent">{project.industry}</span>
                        <span className="text-sm text-muted-foreground">•</span>
                        <span className="text-sm text-muted-foreground">{project.year}</span>
                      </div>
                      <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
                        {project.title}
                      </h2>
                      <p className="text-muted-foreground leading-relaxed mb-6">
                        {project.description}
                      </p>
                      <a
                        href={project.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 text-primary hover:text-accent font-semibold transition-colors"
                      >
                        View Live Project <ArrowUpRight className="w-5 h-5" />
                      </a>
                    </div>
                    <div className={`bg-muted/50 p-8 lg:p-12 flex flex-col justify-center ${index % 2 === 0 ? 'lg:order-2' : 'lg:order-1'}`}>
                      <div className="mb-6">
                        <h3 className="text-sm font-semibold text-foreground mb-3 uppercase tracking-wider">
                          Services Delivered
                        </h3>
                        <div className="flex flex-wrap gap-2">
                          {project.services.map((service) => (
                            <span key={service} className="px-3 py-1 bg-primary/10 text-primary text-sm rounded-full">
                              {service}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-foreground mb-3 uppercase tracking-wider">
                          Key Highlights
                        </h3>
                        <ul className="space-y-2">
                          {project.highlights.map((highlight) => (
                            <li key={highlight} className="flex items-start gap-2 text-sm text-muted-foreground">
                              <ArrowRight className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" />
                              {highlight}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </Card>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 bg-gradient-to-br from-primary/5 via-background to-accent/10">
        <div className="max-w-4xl mx-auto px-4 md:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-6">
            Ready to Start Your Project?
          </h2>
          <p className="text-lg text-muted-foreground mb-8">
            Join our growing list of satisfied clients across Education, Healthcare, and Enterprise sectors
          </p>
          <button
            onClick={() => {
              navigate('/')
              setTimeout(() => {
                document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' })
              }, 100)
            }}
            className="inline-flex items-center justify-center px-8 py-3 bg-accent text-accent-foreground hover:bg-accent/90 font-semibold rounded-md transition-colors"
          >
            Request a Free Consultation
          </button>
        </div>
      </section>
    </div>
  )
}
