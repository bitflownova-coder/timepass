import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { SERVICES } from '@/lib/constants'
import { 
  Brain, 
  ShieldCheck, 
  Code, 
  Lightning, 
  DeviceMobile, 
  ChartLine 
} from '@phosphor-icons/react'

const SERVICE_ICONS = {
  'AI Development': Brain,
  'Cyber Security Services': ShieldCheck,
  'Software Development': Code,
  'Automation Tools': Lightning,
  'App Development': DeviceMobile,
  'Digital Marketing': ChartLine
}

const SERVICE_DESCRIPTIONS = {
  'AI Development': 'Harness the power of artificial intelligence to drive innovation and efficiency',
  'Cyber Security Services': 'Protect your digital assets with enterprise-grade security solutions',
  'Software Development': 'Custom software tailored to your unique business requirements',
  'Automation Tools': 'Streamline operations with intelligent automation workflows',
  'App Development': 'Native and cross-platform mobile applications that users love',
  'Digital Marketing': 'Data-driven strategies to grow your online presence'
}

export function Services() {
  return (
    <section id="services" className="py-20 md:py-24">
      <div className="max-w-7xl mx-auto px-4 md:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-4">
            Our Diverse Services
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Comprehensive digital solutions to power your business forward
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {SERVICES.map((service) => {
            const Icon = SERVICE_ICONS[service]
            return (
              <Card 
                key={service} 
                className="p-8 hover:shadow-xl transition-all hover:scale-105 cursor-pointer group border-2 hover:border-accent/50"
              >
                <div className="w-14 h-14 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <Icon className="w-7 h-7 text-primary-foreground" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-3">
                  {service}
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  {SERVICE_DESCRIPTIONS[service]}
                </p>
              </Card>
            )
          })}
        </div>

        <div className="text-center">
          <Button size="lg" variant="outline" className="gap-2">
            View All Services
          </Button>
        </div>
      </div>
    </section>
  )
}
