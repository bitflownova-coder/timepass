import { Card } from '@/components/ui/card'
import { GraduationCap, Heart, Buildings, Target, Sparkle } from '@phosphor-icons/react'

interface AboutPageProps {
  navigate: (path: string) => void
}

const verticals = [
  {
    icon: GraduationCap,
    name: 'Education',
    description: 'Transforming learning experiences through innovative EdTech platforms, personalized AI-driven education, and comprehensive student management systems'
  },
  {
    icon: Heart,
    name: 'Healthcare',
    description: 'Delivering secure, compliant solutions for medical conferences, patient management, and healthcare data systems with enterprise-grade security'
  },
  {
    icon: Buildings,
    name: 'Enterprise',
    description: 'Scalable digital infrastructure for large organizations, including custom software, automation tools, and cloud-native applications'
  }
]

const founders = [
  {
    name: 'Gauri Dumbare',
    role: 'CEO',
    description: 'Gauri brings a visionary approach to digital transformation, combining strategic business acumen with creative excellence. With a deep passion for design-led experiences, she guides Bitflow Nova\'s mission to deliver solutions that are not only functional but beautiful and intuitive. Her leadership emphasizes the importance of understanding client needs at a fundamental level and translating those insights into innovative digital products. Under her direction, the company has established itself as a trusted partner for organizations seeking to elevate their digital presence through thoughtful design, strategic planning, and user-centered innovation.',
    focus: ['Strategic Vision', 'Creative Excellence', 'Design-Led Experiences', 'Client Partnership']
  },
  {
    name: 'Manthan Pawale',
    role: 'CTO',
    description: 'Manthan is a technology leader specializing in digital transformation and scalable solution architecture. With extensive expertise in feature engineering, cloud infrastructure, and modern development practices, he ensures Bitflow Nova delivers cutting-edge technical solutions. His approach emphasizes building systems that are not only powerful today but can evolve and scale as client needs grow. Manthan\'s commitment to engineering excellence and sustainable practices has enabled the company to maintain its Fast Turnaround promise while never compromising on code quality, security, or performance.',
    focus: ['Digital Transformation', 'Feature Engineering', 'Scalable Solutions', 'Technical Excellence']
  }
]

export function AboutPage({ navigate }: AboutPageProps) {
  return (
    <div className="pt-16">
      <section className="py-20 bg-gradient-to-br from-primary/5 via-background to-accent/10">
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-4">
              About Bitflow Nova
            </h1>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Expert Professionals committed to delivering innovative digital solutions with Unmatched Support
            </p>
          </div>
        </div>
      </section>

      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 md:px-8">
          <div className="flex items-center gap-3 mb-6">
            <Target className="w-8 h-8 text-accent" weight="duotone" />
            <h2 className="text-3xl md:text-4xl font-bold text-foreground">
              Our Mission
            </h2>
          </div>
          <div className="space-y-4 text-lg text-muted-foreground leading-relaxed">
            <p>
              Bitflow Nova exists to transform businesses through the strategic application of digital technology. We believe that every organization—regardless of size or sector—deserves access to world-class digital solutions delivered by Expert Professionals who understand both technology and business.
            </p>
            <p>
              Our mission is to make advanced digital capabilities accessible and affordable through our commitment to Fast Turnaround, Unmatched Support, and Sustainable Practices. We don't just build software; we build partnerships based on trust, transparency, and shared success.
            </p>
            <p>
              By combining technical expertise with genuine care for our clients' outcomes, we've established ourselves as a trusted partner for organizations across Education, Healthcare, and Enterprise sectors. Our 3-week deployment timeline demonstrates that quality and speed are not mutually exclusive when you have the right team and processes in place.
            </p>
          </div>
        </div>
      </section>

      <section className="py-20 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              What We Do
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Specialized digital solutions across three core verticals
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {verticals.map((vertical) => {
              const Icon = vertical.icon
              return (
                <Card key={vertical.name} className="p-8 text-center hover:shadow-lg transition-shadow bg-card">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
                    <Icon className="w-8 h-8 text-primary" weight="duotone" />
                  </div>
                  <h3 className="text-xl font-bold text-foreground mb-3">{vertical.name}</h3>
                  <p className="text-muted-foreground">{vertical.description}</p>
                </Card>
              )
            })}
          </div>
        </div>
      </section>

      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <div className="text-center mb-12">
            <div className="flex items-center justify-center gap-3 mb-4">
              <Sparkle className="w-8 h-8 text-accent" weight="duotone" />
              <h2 className="text-3xl md:text-4xl font-bold text-foreground">
                Meet Our Founders
              </h2>
            </div>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Leadership combining strategic vision with technical excellence
            </p>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            {founders.map((founder) => (
              <Card key={founder.name} className="p-8 bg-card hover:shadow-xl transition-shadow">
                <div className="mb-6">
                  <h3 className="text-2xl font-bold text-foreground mb-1">{founder.name}</h3>
                  <div className="text-accent font-semibold">{founder.role}</div>
                </div>
                <p className="text-muted-foreground leading-relaxed mb-6">
                  {founder.description}
                </p>
                <div>
                  <h4 className="text-sm font-semibold text-foreground mb-3 uppercase tracking-wider">
                    Areas of Focus
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {founder.focus.map((area) => (
                      <span key={area} className="px-3 py-1 bg-primary/10 text-primary text-sm rounded-full">
                        {area}
                      </span>
                    ))}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 bg-gradient-to-br from-primary/5 via-background to-accent/10">
        <div className="max-w-4xl mx-auto px-4 md:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-6">
            Let's Build Something Great Together
          </h2>
          <p className="text-lg text-muted-foreground mb-8">
            Experience the difference that Expert Professionals, Fast Turnaround, and Unmatched Support can make for your organization
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
