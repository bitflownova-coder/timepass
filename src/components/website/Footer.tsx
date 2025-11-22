import { Separator } from '@/components/ui/separator'
import { LinkedinLogo, Envelope } from '@phosphor-icons/react'
import { ContactForm } from '@/components/website/ContactForm'
import { Logo } from '@/components/website/Logo'

interface FooterProps {
  navigate: (path: string) => void
}

export function Footer({ navigate }: FooterProps) {
  const quickLinks = [
    { label: 'Privacy Policy', path: '/privacy-policy' },
    { label: 'Terms and Conditions', path: '/terms-and-conditions' },
    { label: 'Refund Policy', path: '/refund-policy' }
  ]

  return (
    <footer className="bg-card border-t border-border">
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-20">
        <div className="mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground text-center mb-4">
            Request a Free Consultation
          </h2>
          <p className="text-muted-foreground text-center mb-8 max-w-2xl mx-auto">
            Let our Expert Professionals help you achieve Fast Turnaround with Unmatched Support
          </p>
          <ContactForm />
        </div>

        <Separator className="mb-12" />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 mb-12">
          <div>
            <div className="mb-4">
              <Logo />
            </div>
            <p className="text-muted-foreground">
              Expert Professionals delivering innovative digital solutions with Sustainable Practices
            </p>
          </div>

          <div>
            <h3 className="font-semibold text-foreground mb-4">Quick Links</h3>
            <div className="flex flex-col gap-3">
              {quickLinks.map((link) => (
                <button
                  key={link.path}
                  onClick={() => navigate(link.path)}
                  className="text-muted-foreground hover:text-primary transition-colors text-left text-sm"
                >
                  {link.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-foreground mb-4">Contact</h3>
            <div className="flex flex-col gap-3">
              <a
                href="mailto:bitflownova@gmail.com"
                className="text-muted-foreground hover:text-primary transition-colors flex items-center gap-2 text-sm"
              >
                <Envelope className="w-5 h-5" />
                bitflownova@gmail.com
              </a>
              <a
                href="https://www.linkedin.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-primary transition-colors flex items-center gap-2 text-sm"
              >
                <LinkedinLogo className="w-5 h-5" weight="fill" />
                Follow us on LinkedIn
              </a>
            </div>
          </div>
        </div>

        <Separator className="mb-8" />

        <div className="text-center text-sm text-muted-foreground">
          <p>&copy; {new Date().getFullYear()} Bitflow Nova. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}
