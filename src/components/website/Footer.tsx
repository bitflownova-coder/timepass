import { Separator } from '@/components/ui/separator'
import { 
  GithubLogo, 
  TwitterLogo, 
  LinkedinLogo, 
  InstagramLogo 
} from '@phosphor-icons/react'

interface FooterProps {
  onContactClick: () => void
}

export function Footer({ onContactClick }: FooterProps) {
  const scrollToSection = (id: string) => {
    const section = document.getElementById(id)
    if (section) {
      section.scrollIntoView({ behavior: 'smooth' })
    }
  }

  const navLinks = [
    { label: 'Home', id: 'hero' },
    { label: 'Our Work', id: 'projects' },
    { label: 'About', id: 'why-choose-us' },
    { label: 'Services', id: 'services' },
    { label: 'Contact', id: 'contact' }
  ]

  const socialLinks = [
    { icon: GithubLogo, href: '#', label: 'GitHub' },
    { icon: TwitterLogo, href: '#', label: 'Twitter' },
    { icon: LinkedinLogo, href: '#', label: 'LinkedIn' },
    { icon: InstagramLogo, href: '#', label: 'Instagram' }
  ]

  return (
    <footer className="bg-card border-t border-border">
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-gradient-to-br from-primary to-accent rounded-md" />
              <span className="text-xl font-bold text-foreground">Bitflow Nova</span>
            </div>
            <p className="text-muted-foreground">
              Transforming businesses through innovative digital solutions.
            </p>
          </div>

          <div>
            <h3 className="font-semibold text-foreground mb-4">Quick Links</h3>
            <div className="flex flex-col gap-2">
              {navLinks.map((link) => (
                <button
                  key={link.id}
                  onClick={() => scrollToSection(link.id)}
                  className="text-muted-foreground hover:text-accent transition-colors text-left"
                >
                  {link.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-foreground mb-4">Follow Us</h3>
            <div className="flex gap-3">
              {socialLinks.map((social) => {
                const Icon = social.icon
                return (
                  <a
                    key={social.label}
                    href={social.href}
                    aria-label={social.label}
                    className="w-10 h-10 rounded-lg bg-muted hover:bg-accent hover:text-accent-foreground transition-colors flex items-center justify-center"
                  >
                    <Icon className="w-5 h-5" />
                  </a>
                )
              })}
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
