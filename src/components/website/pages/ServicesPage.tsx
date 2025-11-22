import { Card } from '@/components/ui/card'
import { 
  Brain, 
  ShieldCheck, 
  Code, 
  Lightning, 
  DeviceMobile, 
  ChartLine,
  Globe,
  Database,
  MagnifyingGlass
} from '@phosphor-icons/react'

interface ServicesPageProps {
  navigate: (path: string) => void
}

const services = [
  {
    icon: Brain,
    name: 'AI Development',
    description: 'Harness the power of artificial intelligence to automate processes, gain insights, and deliver personalized experiences. Our Expert Professionals build custom machine learning models, natural language processing solutions, and predictive analytics platforms.',
    features: ['Machine Learning Models', 'Natural Language Processing', 'Computer Vision', 'Predictive Analytics']
  },
  {
    icon: ShieldCheck,
    name: 'Cyber Security',
    description: 'Protect your digital assets with enterprise-grade security infrastructure. We implement comprehensive security strategies including penetration testing, vulnerability assessments, and compliance frameworks with Unmatched Support.',
    features: ['Penetration Testing', 'Security Audits', 'Compliance Management', '24/7 Monitoring']
  },
  {
    icon: Code,
    name: 'Software Development',
    description: 'Custom software engineered for scale and performance. Our development teams deliver robust, maintainable solutions using modern architectures and best practices, ensuring Fast Turnaround without compromising quality.',
    features: ['Custom Applications', 'API Development', 'Cloud-Native Solutions', 'Legacy Modernization']
  },
  {
    icon: Lightning,
    name: 'Automation Tools',
    description: 'Streamline operations and boost efficiency with intelligent automation. We design and implement workflow automation, robotic process automation (RPA), and integration solutions that reduce manual effort and errors.',
    features: ['Workflow Automation', 'RPA Solutions', 'System Integration', 'Process Optimization']
  },
  {
    icon: DeviceMobile,
    name: 'App Development',
    description: 'Native and cross-platform mobile applications that deliver exceptional user experiences. From iOS and Android to hybrid solutions, our Expert Professionals build apps that engage users and drive business results.',
    features: ['iOS & Android', 'Cross-Platform Apps', 'App Modernization', 'App Store Optimization']
  },
  {
    icon: ChartLine,
    name: 'Digital Marketing',
    description: 'Data-driven growth strategies that deliver measurable results. Our marketing experts leverage analytics, SEO, content marketing, and paid advertising to increase visibility and drive conversions with Sustainable Practices.',
    features: ['Marketing Strategy', 'Analytics & Reporting', 'Content Marketing', 'Paid Advertising']
  },
  {
    icon: Globe,
    name: 'Web Development',
    description: 'Modern, responsive web experiences built with cutting-edge technologies. We create high-performance websites and web applications that look stunning, load fast, and convert visitors into customers.',
    features: ['Responsive Design', 'Progressive Web Apps', 'E-commerce Solutions', 'Performance Optimization']
  },
  {
    icon: Database,
    name: 'CMS Development',
    description: 'Powerful content management systems that put you in control. We build custom CMS solutions and implement platforms like WordPress, Drupal, and headless CMS architectures for maximum flexibility.',
    features: ['Custom CMS', 'Headless Architecture', 'Content Strategy', 'Multi-site Management']
  },
  {
    icon: MagnifyingGlass,
    name: 'SEO',
    description: 'Optimize visibility and organic reach with comprehensive search engine optimization. Our SEO specialists conduct technical audits, keyword research, and implement strategies that improve rankings and drive qualified traffic.',
    features: ['Technical SEO', 'Keyword Research', 'Link Building', 'Local SEO']
  }
]

export function ServicesPage({ navigate }: ServicesPageProps) {
  return (
    <div className="pt-16">
      <section className="py-20 bg-gradient-to-br from-primary/5 via-background to-accent/10">
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-4">
              Comprehensive Digital Solutions
            </h1>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Expert Professionals delivering nine core services with Fast Turnaround, Unmatched Support, and Sustainable Practices
            </p>
          </div>
        </div>
      </section>

      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <div className="grid grid-cols-1 gap-12">
            {services.map((service, index) => {
              const Icon = service.icon
              return (
                <Card key={service.name} className={`p-8 hover:shadow-xl transition-shadow ${index % 2 === 0 ? 'bg-card' : 'bg-muted/30'}`}>
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-2">
                      <div className="flex items-start gap-4 mb-4">
                        <div className="flex-shrink-0">
                          <div className="inline-flex items-center justify-center w-16 h-16 rounded-lg bg-primary/10">
                            <Icon className="w-8 h-8 text-primary" weight="duotone" />
                          </div>
                        </div>
                        <div>
                          <h2 className="text-2xl font-bold text-foreground mb-2">{service.name}</h2>
                          <p className="text-muted-foreground leading-relaxed">{service.description}</p>
                        </div>
                      </div>
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-foreground mb-3 uppercase tracking-wider">Key Capabilities</h3>
                      <ul className="space-y-2">
                        {service.features.map((feature) => (
                          <li key={feature} className="flex items-start gap-2 text-sm text-muted-foreground">
                            <span className="text-accent mt-1">•</span>
                            {feature}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </Card>
              )
            })}
          </div>
        </div>
      </section>

      <section className="py-20 bg-gradient-to-br from-primary/5 via-background to-accent/10">
        <div className="max-w-4xl mx-auto px-4 md:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-6">
            Ready to Get Started?
          </h2>
          <p className="text-lg text-muted-foreground mb-8">
            Our Expert Professionals are ready to discuss your project and deliver solutions with Fast Turnaround
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
