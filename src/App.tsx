import { useState, useEffect } from 'react'
import { Navbar } from '@/components/website/Navbar'
import { Footer } from '@/components/website/Footer'
import { HomePage } from '@/components/website/pages/HomePage'
import { ServicesPage } from '@/components/website/pages/ServicesPage'
import { ProjectsPage } from '@/components/website/pages/ProjectsPage'
import { AboutPage } from '@/components/website/pages/AboutPage'
import { PrivacyPolicyPage } from '@/components/website/pages/PrivacyPolicyPage'
import { TermsAndConditionsPage } from '@/components/website/pages/TermsAndConditionsPage'
import { RefundPolicyPage } from '@/components/website/pages/RefundPolicyPage'

function App() {
  const [currentPath, setCurrentPath] = useState(window.location.pathname)

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname)
    }

    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const navigate = (path: string) => {
    window.history.pushState({}, '', path)
    setCurrentPath(path)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const renderPage = () => {
    switch (currentPath) {
      case '/':
        return <HomePage navigate={navigate} />
      case '/services':
        return <ServicesPage navigate={navigate} />
      case '/s-projects-side-by-side':
        return <ProjectsPage navigate={navigate} />
      case '/about':
        return <AboutPage navigate={navigate} />
      case '/privacy-policy':
        return <PrivacyPolicyPage navigate={navigate} />
      case '/terms-and-conditions':
        return <TermsAndConditionsPage navigate={navigate} />
      case '/refund-policy':
        return <RefundPolicyPage navigate={navigate} />
      default:
        return <HomePage navigate={navigate} />
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar currentPath={currentPath} navigate={navigate} />
      {renderPage()}
      <Footer navigate={navigate} />
    </div>
  )
}

export default App
