import { useState } from 'react'
import { useTheme } from '@/hooks/use-theme'
import { Navbar } from '@/components/website/Navbar'
import { Hero } from '@/components/website/Hero'
import { Process } from '@/components/website/Process'
import { Services } from '@/components/website/Services'
import { Projects } from '@/components/website/Projects'
import { WhyChooseUs } from '@/components/website/WhyChooseUs'
import { Contact } from '@/components/website/Contact'
import { Footer } from '@/components/website/Footer'

function App() {
  useTheme()
  const [showContact, setShowContact] = useState(false)

  const scrollToContact = () => {
    const contactSection = document.getElementById('contact')
    if (contactSection) {
      contactSection.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar onContactClick={scrollToContact} />
      <Hero onConsultationClick={scrollToContact} onContactClick={scrollToContact} />
      <Process />
      <Services />
      <Projects />
      <WhyChooseUs />
      <Contact />
      <Footer onContactClick={scrollToContact} />
    </div>
  )
}

export default App
