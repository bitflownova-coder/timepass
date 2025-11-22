import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { ContactForm } from '@/components/website/ContactForm'
import { 
  Brain, 
  ShieldCheck, 
  Code, 
  Lightning, 
  DeviceMobile, 
  ChartLine,
  Globe,
  Database,
  MagnifyingGlass,
  ArrowRight,
  CheckCircle,
  Users,
  Headset,
  Clock,
  Leaf
} from '@phosphor-icons/react'

interface HomePageProps {
  navigate: (path: string) => void
}

const services = [
  { icon: Brain, name: 'AI Development', description: 'Intelligent automation and machine learning solutions' },
  { icon: ShieldCheck, name: 'Cyber Security', description: 'Enterprise-grade security infrastructure' },
  { icon: Code, name: 'Software Development', description: 'Custom software engineered for scale' },
  { icon: Lightning, name: 'Automation Tools', description: 'Streamline operations and boost efficiency' },
  { icon: DeviceMobile, name: 'App Development', description: 'Native and cross-platform applications' },
  { icon: ChartLine, name: 'Digital Marketing', description: 'Data-driven growth strategies' },
  { icon: Globe, name: 'Web Development', description: 'Modern, responsive web experiences' },
  { icon: Database, name: 'CMS Development', description: 'Powerful content management systems' },
  { icon: MagnifyingGlass, name: 'SEO', description: 'Optimize visibility and organic reach' }
]

const differentiators = [
  {
    icon: Users,
    title: 'Expert Professionals',
    description: 'Our team brings deep expertise across technology, design, and business strategy'
  },
  {
    icon: Headset,
    title: 'Unmatched Support',
    description: 'Dedicated account management and 24/7 technical support for peace of mind'
  },
  {
    icon: Clock,
    title: 'Fast Turnaround',
    description: '3-week deployment timeline: 1 week solution design, 2 weeks implementation'
  },
  {
    icon: Leaf,
    title: 'Sustainable Practices',
    description: 'Environmentally conscious development with long-term scalability'
  }
]

const projects = [
  {
    title: 'Sage Helix 360',
    industry: 'Education',
    description: 'Comprehensive EdTech platform transformation integrating modern web technologies and CMS capabilities. Leveraged AI Development to create personalized learning pathways that adapt to individual student needs and performance metrics. The solution seamlessly combines content delivery, student engagement tools, and advanced analytics to drive educational outcomes. Our Expert Professionals delivered a scalable architecture supporting thousands of concurrent users while maintaining exceptional performance.',
    url: 'https://sage-edu.in/',
    services: ['Web Development', 'CMS Integration', 'AI Development']
  },
  {
    title: 'APPICON 2024',
    industry: 'Healthcare',
    description: 'Large-scale medical conference platform featuring automated registration workflows and comprehensive attendee management. Built custom App Development solutions to streamline check-in processes and real-time session tracking. Integrated Digital Marketing automation to drive registration conversions and engagement. The platform successfully handled complex multi-track scheduling while ensuring data security compliance for sensitive healthcare professional information, showcasing our Unmatched Support throughout the event lifecycle.',
    url: 'https://www.appicon2024chennai.com/',
    services: ['App Development', 'Digital Marketing', 'Automation']
  },
  {
    title: 'Forensic Medicon 2025',
    industry: 'Healthcare / Enterprise',
    description: 'Mission-critical conference platform deployed with enterprise-grade Cyber Security infrastructure protecting sensitive forensic data. Delivered comprehensive Web Development solution with robust authentication and encrypted data transmission. The project exemplifies our Fast Turnaround capability, completed from requirements to production in just 3 weeks without compromising security standards. Built scalable cloud infrastructure supporting peak load during registration periods while maintaining HIPAA compliance for healthcare data handling.',
    url: 'https://www.forensicmedicon2025chennai.com/',
    services: ['Cyber Security', 'Web Development', 'Cloud Infrastructure']
  }
]

const processSteps = [
  {
    number: '01',
    title: 'Discuss Requirements',
    description: 'We begin with a thorough consultation to understand your business objectives and technical needs'
  },
  {
    number: '02',
    title: 'Craft Solution (1 Week)',
    description: 'Our Expert Professionals design a comprehensive solution architecture tailored to your goals'
  },
  {
    number: '03',
    title: 'Implementation (2 Weeks)',
    description: 'Rapid development and deployment using best practices and proven methodologies'
  },
  {
    number: '04',
    title: 'Experience Results',
    description: 'Launch with confidence backed by Unmatched Support and ongoing optimization'
  }
]

export function HomePage({ navigate }: HomePageProps) {
  const scrollToContact = () => {
    const contactSection = document.getElementById('contact')
    contactSection?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="pt-16">
      <section id="hero" className="relative min-h-[90vh] flex items-center justify-center bg-gradient-to-br from-primary/5 via-background to-accent/10">
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-20">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-foreground leading-tight">
                Design. Protect. automate.
              </h1>
              <p className="text-xl text-muted-foreground leading-relaxed">
                Expert Professionals delivering innovative digital solutions with Fast Turnaround and Unmatched Support for enterprise clients
              </p>
              <div className="flex flex-wrap gap-4 pt-4">
                <Button
                  size="lg"
                  onClick={scrollToContact}
                  className="bg-accent text-accent-foreground hover:bg-accent/90 font-semibold"
                >
                  Request a Free Consultation
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  onClick={() => navigate('/s-projects-side-by-side')}
                >
                  View Our Work
                </Button>
              </div>
            </div>
            <div className="hidden lg:block">
              <ContactForm />
            </div>
          </div>
          <div className="lg:hidden mt-12">
            <ContactForm />
          </div>
        </div>
      </section>

      <section id="services" className="py-20 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Our Diverse Services
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Comprehensive digital solutions powered by Expert Professionals across nine core competencies
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {services.map((service) => {
              const Icon = service.icon
              return (
                <Card key={service.name} className="p-6 hover:shadow-lg transition-shadow bg-card">
                  <Icon className="w-12 h-12 text-primary mb-4" weight="duotone" />
                  <h3 className="text-lg font-semibold text-foreground mb-2">{service.name}</h3>
                  <p className="text-muted-foreground text-sm">{service.description}</p>
                </Card>
              )
            })}
          </div>
          <div className="text-center mt-8">
            <Button
              variant="outline"
              size="lg"
              onClick={() => navigate('/services')}
            >
              View All Services
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </div>
        </div>
      </section>

      <section id="differentiators" className="py-20">
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Why Choose Bitflow Nova
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Four pillars of excellence that set us apart in digital solutions
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {differentiators.map((item) => {
              const Icon = item.icon
              return (
                <Card key={item.title} className="p-6 text-center hover:shadow-lg transition-shadow bg-card">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
                    <Icon className="w-8 h-8 text-primary" weight="duotone" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">{item.title}</h3>
                  <p className="text-muted-foreground text-sm">{item.description}</p>
                </Card>
              )
            })}
          </div>
        </div>
      </section>

      <section id="process" className="py-20 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Our Proven Process
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              <strong className="text-accent">3-Week Deployment Timeline</strong> – From concept to production with Fast Turnaround
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {processSteps.map((step, index) => (
              <div key={step.number} className="relative">
                <Card className="p-6 h-full bg-card">
                  <div className="text-5xl font-bold text-accent/20 mb-4">{step.number}</div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">{step.title}</h3>
                  <p className="text-muted-foreground text-sm">{step.description}</p>
                </Card>
                {index < processSteps.length - 1 && (
                  <div className="hidden lg:block absolute top-1/2 -right-4 transform -translate-y-1/2">
                    <ArrowRight className="w-6 h-6 text-accent" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="portfolio" className="py-20">
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Featured Projects
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Real-world results across Education, Healthcare, and Enterprise verticals
            </p>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {projects.map((project) => (
              <Card key={project.title} className="p-6 hover:shadow-xl transition-shadow bg-card flex flex-col">
                <div className="mb-4">
                  <div className="text-sm text-accent font-semibold mb-2">{project.industry}</div>
                  <h3 className="text-xl font-bold text-foreground mb-3">{project.title}</h3>
                  <p className="text-muted-foreground text-sm leading-relaxed mb-4">
                    {project.description}
                  </p>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {project.services.map((service) => (
                      <span key={service} className="text-xs px-3 py-1 bg-primary/10 text-primary rounded-full">
                        {service}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="mt-auto">
                  <a
                    href={project.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:text-accent font-medium text-sm inline-flex items-center gap-1"
                  >
                    View Project <ArrowRight className="w-4 h-4" />
                  </a>
                </div>
              </Card>
            ))}
          </div>
          <div className="text-center mt-8">
            <Button
              variant="outline"
              size="lg"
              onClick={() => navigate('/s-projects-side-by-side')}
            >
              View All Projects
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </div>
        </div>
      </section>

      <section id="contact" className="py-20 bg-gradient-to-br from-primary/5 via-background to-accent/10">
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Ready to Transform Your Business?
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Connect with our Expert Professionals for a free consultation and experience Fast Turnaround with Unmatched Support
            </p>
          </div>
          <ContactForm />
        </div>
      </section>
    </div>
  )
}
