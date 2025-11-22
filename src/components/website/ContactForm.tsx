import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card } from '@/components/ui/card'
import { toast } from 'sonner'
import { useKV } from '@github/spark/hooks'

interface FormData {
  firstName: string
  lastName: string
  email: string
  phone: string
  service: string
}

const services = [
  'AI Development',
  'Cyber Security',
  'Software Development',
  'Automation Tools',
  'App Development',
  'Digital Marketing',
  'Web Development',
  'CMS Development',
  'SEO'
]

export function ContactForm() {
  const [formData, setFormData] = useState<FormData>({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    service: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submissions, setSubmissions] = useKV<any[]>('contact-submissions', [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.firstName || !formData.lastName || !formData.email || !formData.phone || !formData.service) {
      toast.error('Please fill in all fields')
      return
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(formData.email)) {
      toast.error('Please enter a valid email address')
      return
    }

    setIsSubmitting(true)

    try {
      const submission = {
        ...formData,
        timestamp: new Date().toISOString(),
        id: Date.now()
      }
      
      setSubmissions((current) => [...(current || []), submission])
      
      toast.success('Thank you! We\'ll be in touch soon.')
      
      setFormData({
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        service: ''
      })
    } catch (error) {
      toast.error('Something went wrong. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Card className="max-w-3xl mx-auto p-8 bg-card shadow-lg">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label htmlFor="firstName" className="text-foreground font-medium">
              First Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="firstName"
              type="text"
              value={formData.firstName}
              onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
              placeholder="John"
              required
              className="bg-background"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="lastName" className="text-foreground font-medium">
              Last Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="lastName"
              type="text"
              value={formData.lastName}
              onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
              placeholder="Doe"
              required
              className="bg-background"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="email" className="text-foreground font-medium">
            Email <span className="text-destructive">*</span>
          </Label>
          <Input
            id="email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="john.doe@company.com"
            required
            className="bg-background"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="phone" className="text-foreground font-medium">
            Phone Number <span className="text-destructive">*</span>
          </Label>
          <Input
            id="phone"
            type="tel"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            placeholder="+1 (555) 123-4567"
            required
            className="bg-background"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="service" className="text-foreground font-medium">
            Service Choice <span className="text-destructive">*</span>
          </Label>
          <Select
            value={formData.service}
            onValueChange={(value) => setFormData({ ...formData, service: value })}
            required
          >
            <SelectTrigger id="service" className="bg-background">
              <SelectValue placeholder="Select a service" />
            </SelectTrigger>
            <SelectContent>
              {services.map((service) => (
                <SelectItem key={service} value={service}>
                  {service}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button
          type="submit"
          className="w-full bg-accent text-accent-foreground hover:bg-accent/90 font-semibold text-base py-6"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Submitting...' : 'Request a Quote'}
        </Button>
      </form>
    </Card>
  )
}
