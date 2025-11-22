import { Button } from '@/components/ui/button'
import { ArrowRight } from '@phosphor-icons/react'
import { SpiralAnimation } from '@/components/ui/spiral-animation'

interface HeroProps {
  onConsultationClick: () => void
  onContactClick: () => void
}

export function Hero({ onConsultationClick, onContactClick }: HeroProps) {
  return (
    <section id="hero" className="relative min-h-screen flex items-center justify-center pt-16 overflow-hidden">
      <div className="absolute inset-0 opacity-20">
        <SpiralAnimation />
      </div>
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background/50 to-accent/5" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_120%,rgba(120,119,198,0.1),rgba(255,255,255,0))]" />
      
      <div className="relative max-w-7xl mx-auto px-4 md:px-8 py-20 text-center">
        <div className="space-y-8">
          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-foreground tracking-tight">
            Design. Protect. Automate.
          </h1>
          
          <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto">
            Transforming businesses through innovative digital solutions, cutting-edge AI, and robust cybersecurity
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Button 
              size="lg" 
              className="gap-2 text-base px-8"
              onClick={onConsultationClick}
            >
              Request a Free Consultation
              <ArrowRight className="w-5 h-5" />
            </Button>
            <Button 
              size="lg" 
              variant="outline"
              className="text-base px-8"
              onClick={onContactClick}
            >
              Contact Us
            </Button>
          </div>
        </div>

        <div className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto">
          <div className="space-y-2">
            <div className="text-3xl md:text-4xl font-bold text-accent">500+</div>
            <div className="text-sm text-muted-foreground">Projects Delivered</div>
          </div>
          <div className="space-y-2">
            <div className="text-3xl md:text-4xl font-bold text-accent">98%</div>
            <div className="text-sm text-muted-foreground">Client Satisfaction</div>
          </div>
          <div className="space-y-2">
            <div className="text-3xl md:text-4xl font-bold text-accent">24/7</div>
            <div className="text-sm text-muted-foreground">Support Available</div>
          </div>
          <div className="space-y-2">
            <div className="text-3xl md:text-4xl font-bold text-accent">10+</div>
            <div className="text-sm text-muted-foreground">Years Experience</div>
          </div>
        </div>
      </div>
    </section>
  )
}
