import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ArrowRight } from '@phosphor-icons/react'

export function Projects() {
  return (
    <section id="projects" className="py-20 md:py-24 bg-muted/30">
      <div className="max-w-7xl mx-auto px-4 md:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-4">
            Our Work in Action
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Delivering exceptional results for our clients
          </p>
        </div>

        <Card className="overflow-hidden hover:shadow-2xl transition-shadow">
          <div className="grid md:grid-cols-2 gap-0">
            <div className="bg-gradient-to-br from-primary/20 to-accent/20 p-12 flex items-center justify-center">
              <div className="text-center space-y-4">
                <div className="w-24 h-24 mx-auto rounded-2xl bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                  <span className="text-4xl font-bold text-primary-foreground">SH</span>
                </div>
                <h3 className="text-3xl font-bold text-foreground">Sage Helix 360</h3>
              </div>
            </div>
            
            <div className="p-8 md:p-12 flex flex-col justify-center">
              <div className="space-y-4">
                <div className="flex flex-wrap gap-2 mb-4">
                  <Badge variant="secondary">AI Integration</Badge>
                  <Badge variant="secondary">Cloud Architecture</Badge>
                  <Badge variant="secondary">Analytics</Badge>
                </div>
                
                <h4 className="text-2xl font-semibold text-foreground">
                  Enterprise AI Platform
                </h4>
                
                <p className="text-muted-foreground leading-relaxed">
                  A comprehensive AI-powered analytics platform that transformed how Sage Helix processes 
                  and interprets complex data sets. Our solution reduced processing time by 70% while 
                  increasing accuracy and providing real-time insights to decision makers.
                </p>

                <div className="grid grid-cols-3 gap-4 pt-4">
                  <div>
                    <div className="text-2xl font-bold text-accent">70%</div>
                    <div className="text-sm text-muted-foreground">Faster Processing</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-accent">99.9%</div>
                    <div className="text-sm text-muted-foreground">Uptime</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-accent">50K+</div>
                    <div className="text-sm text-muted-foreground">Daily Users</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>

        <div className="text-center mt-12">
          <Button size="lg" variant="outline" className="gap-2">
            View All Projects
            <ArrowRight className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </section>
  )
}
