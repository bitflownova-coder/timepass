export interface QuoteRequest {
  id: string
  firstName: string
  lastName: string
  email: string
  phone: string
  service: string
  createdAt: string
}

export type ServiceType = 
  | 'AI Development'
  | 'Cyber Security Services'
  | 'Software Development'
  | 'Automation Tools'
  | 'App Development'
  | 'Digital Marketing'
