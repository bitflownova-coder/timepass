import { Button } from '@/components/ui/button'
import { List, X } from '@phosphor-icons/react'
import { useState } from 'react'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'

interface NavbarProps {
  currentPath: string
  navigate: (path: string) => void
}

export function Navbar({ currentPath, navigate }: NavbarProps) {
  const [isOpen, setIsOpen] = useState(false)

  const scrollToContact = () => {
    const contactSection = document.getElementById('contact')
    if (contactSection) {
      contactSection.scrollIntoView({ behavior: 'smooth' })
      setIsOpen(false)
    } else {
      navigate('/')
      setTimeout(() => {
        const section = document.getElementById('contact')
        section?.scrollIntoView({ behavior: 'smooth' })
      }, 100)
    }
  }

  const navLinks = [
    { label: 'Home', path: '/' },
    { label: 'Our Work', path: '/s-projects-side-by-side' },
    { label: 'About', path: '/about' }
  ]

  const handleNavClick = (path: string) => {
    navigate(path)
    setIsOpen(false)
  }

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-card/95 backdrop-blur-sm border-b border-border shadow-sm">
      <div className="max-w-7xl mx-auto px-4 md:px-8">
        <div className="flex items-center justify-between h-16">
          <button 
            onClick={() => handleNavClick('/')}
            className="flex flex-col items-start gap-0 hover:opacity-80 transition-opacity"
          >
            <div className="text-xl md:text-2xl font-bold text-foreground tracking-tight">
              # BITFLOW #
            </div>
            <div className="text-xs md:text-sm text-muted-foreground font-medium">
              Design. Protect. automate.
            </div>
          </button>

          <div className="hidden md:flex items-center gap-6">
            {navLinks.map((link) => (
              <button
                key={link.path}
                onClick={() => handleNavClick(link.path)}
                className={`text-sm font-medium transition-colors ${
                  currentPath === link.path
                    ? 'text-primary'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {link.label}
              </button>
            ))}
            
            <Button 
              onClick={scrollToContact}
              className="bg-accent text-accent-foreground hover:bg-accent/90 font-semibold"
            >
              Contact Us
            </Button>
          </div>

          <Sheet open={isOpen} onOpenChange={setIsOpen}>
            <SheetTrigger asChild className="md:hidden">
              <Button variant="ghost" size="icon">
                <List className="w-6 h-6" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-64">
              <div className="flex flex-col gap-6 mt-8">
                {navLinks.map((link) => (
                  <button
                    key={link.path}
                    onClick={() => handleNavClick(link.path)}
                    className={`text-left text-base font-medium transition-colors ${
                      currentPath === link.path
                        ? 'text-primary'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    {link.label}
                  </button>
                ))}
                
                <Button 
                  onClick={scrollToContact}
                  className="bg-accent text-accent-foreground hover:bg-accent/90 font-semibold w-full"
                >
                  Contact Us
                </Button>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </nav>
  )
}
