import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { SERVICES } from '@/lib/constants'
import RadialOrbitalTimeline from '@/components/ui/radial-orbital-timeline'
import { useState } from 'react'
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

const SERVICE_TIMELINE_DATA = [
  {
    id: 1,
    title: 'AI Development',
    date: 'Core Service',
    content: 'Harness the power of artificial intelligence to drive innovation and efficiency in your business operations.',
    category: 'Development',
    icon: Brain,
    relatedIds: [3, 4],
    status: 'completed' as const,
    energy: 95,
  },
  {
    id: 2,
    title: 'Cyber Security',
    date: 'Core Service',
    content: 'Protect your digital assets with enterprise-grade security solutions and proactive threat monitoring.',
    category: 'Security',
    icon: ShieldCheck,
    relatedIds: [3, 1],
    status: 'completed' as const,
    energy: 100,
  },
  {
    id: 3,
    title: 'Software Development',
    date: 'Core Service',
    content: 'Custom software tailored to your unique business requirements with scalable architecture.',
    category: 'Development',
    icon: Code,
    relatedIds: [1, 2, 5],
    status: 'completed' as const,
    energy: 100,
  },
  {
    id: 4,
    title: 'Automation Tools',
    date: 'Core Service',
    content: 'Streamline operations with intelligent automation workflows that save time and reduce costs.',
    category: 'Automation',
    icon: Lightning,
    relatedIds: [1, 5],
    status: 'in-progress' as const,
    energy: 85,
  },
  {
    id: 5,
    title: 'App Development',
    date: 'Core Service',
    content: 'Native and cross-platform mobile applications that users love, built with modern frameworks.',
    category: 'Development',
    icon: DeviceMobile,
    relatedIds: [3, 4, 6],
    status: 'completed' as const,
    energy: 90,
  },
  {
    id: 6,
    title: 'Digital Marketing',
    date: 'Core Service',
    content: 'Data-driven strategies to grow your online presence and reach your target audience effectively.',
    category: 'Marketing',
    icon: ChartLine,
    relatedIds: [5],
    status: 'completed' as const,
    energy: 80,
  },
]

export function Services() {
  const [viewMode, setViewMode] = useState<'grid' | 'orbital'>('grid')

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
          
          <div className="flex justify-center gap-4 mt-8">
            <Button 
              onClick={() => setViewMode('grid')}
              variant={viewMode === 'grid' ? 'default' : 'outline'}
            >
              Grid View
            </Button>
            <Button 
              onClick={() => setViewMode('orbital')}
              variant={viewMode === 'orbital' ? 'default' : 'outline'}
            >
              Orbital View
            </Button>
          </div>
        </div>

        {viewMode === 'grid' ? (
          <>
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
          </>
        ) : (
          <div className="h-screen -mx-4 md:-mx-8">
            <RadialOrbitalTimeline timelineData={SERVICE_TIMELINE_DATA} />
          </div>
        )}
      </div>
    </section>
  )
}
