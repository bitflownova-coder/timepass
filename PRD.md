# BitflowNova Expense Management System

A professional expense management platform for BitflowNova that enables employees to track expenses, manage budgets, and analyze spending patterns with secure authentication.

**Experience Qualities**: 
1. **Professional** - Clean, corporate interface that inspires trust and efficiency
2. **Intuitive** - Seamless navigation and clear information hierarchy for quick task completion
3. **Secure** - Authentication-first approach with user context throughout

**Complexity Level**: Light Application (multiple features with basic state)
- Includes user authentication, expense tracking, budget management, and analytics with persistent state

## Essential Features

### User Authentication
- **Functionality**: Secure login system with company branding
- **Purpose**: Ensure only authorized BitflowNova employees can access expense data
- **Trigger**: Landing page displays login form for unauthenticated users
- **Progression**: User enters email/password → validates credentials → redirects to dashboard
- **Success criteria**: User session persists across page reloads, logout clears session

### Expense Tracking
- **Functionality**: Add, edit, and delete expenses with categorization
- **Purpose**: Maintain accurate records of company spending
- **Trigger**: Click "Add Expense" button or edit existing expense
- **Progression**: Click button → dialog opens → fill form (amount in ₹, category, description, date) → save → updates list
- **Success criteria**: Expenses persist in storage, display in INR format, sorted by date

### Budget Management
- **Functionality**: Set category-wise budget limits in INR
- **Purpose**: Control spending and prevent budget overruns
- **Trigger**: Navigate to Budgets tab
- **Progression**: View category cards → click edit → set budget amount → save → shows spent vs budget
- **Success criteria**: Visual indicators for budget status, alerts when over budget

### Spending Analytics
- **Functionality**: Visual charts showing spending trends over time
- **Purpose**: Identify patterns and optimize spending decisions
- **Trigger**: Navigate to Trends tab
- **Progression**: Select tab → view category breakdown chart → view monthly trend chart → analyze patterns
- **Success criteria**: Charts update dynamically with expense data, show meaningful insights

## Edge Case Handling
- **Empty States**: First-time users see helpful prompts to add expenses or set budgets
- **Over Budget**: Alert banner displays when any category exceeds budget limit
- **Invalid Login**: Clear error messages for incorrect credentials
- **Missing Data**: Graceful handling of zero budgets or expenses
- **Date Range**: Automatically filter expenses by current month, with historical data available

## Design Direction
The design should evoke professionalism, trust, and technological sophistication - similar to edu-bit's clean corporate aesthetic but with a unique BitflowNova identity. The interface should feel modern and efficient with a tech-forward vibe, using a minimal approach that emphasizes content and data clarity over decorative elements.

## Color Selection
Custom palette inspired by the BitflowNova logo (navy blue with cyan accents)

- **Primary Color**: Deep Navy (oklch(0.25 0.05 250)) - Represents professionalism, trust, and corporate stability
- **Secondary Colors**: Slate Gray (oklch(0.45 0.02 250)) for supporting elements, Light Blue-Gray backgrounds (oklch(0.97 0.01 250))
- **Accent Color**: Cyan Blue (oklch(0.65 0.15 200)) - Tech-forward highlight for CTAs and active states, draws from logo's cyan elements
- **Foreground/Background Pairings**: 
  - Background (Light Blue-Gray oklch(0.97 0.01 250)): Dark Navy text (oklch(0.25 0.05 250)) - Ratio 8.5:1 ✓
  - Card (White oklch(1 0 0)): Dark Navy text (oklch(0.25 0.05 250)) - Ratio 11.2:1 ✓
  - Primary (Navy oklch(0.25 0.05 250)): White text (oklch(1 0 0)) - Ratio 11.2:1 ✓
  - Accent (Cyan oklch(0.65 0.15 200)): White text (oklch(1 0 0)) - Ratio 5.2:1 ✓
  - Secondary (Slate oklch(0.45 0.02 250)): White text (oklch(1 0 0)) - Ratio 7.1:1 ✓

## Font Selection
The typeface should convey modern professionalism with excellent readability for financial data. Inter font family provides technical precision with geometric proportions, perfect for a tech company's expense platform.

- **Typographic Hierarchy**: 
  - H1 (Page Title): Inter Semibold/32px/tight letter spacing
  - H2 (Section Headers): Inter Medium/24px/normal spacing
  - H3 (Card Titles): Inter Medium/18px/normal spacing
  - Body (Content): Inter Regular/16px/relaxed line height
  - Caption (Meta info): Inter Regular/14px/tabular numbers for amounts
  - Button Labels: Inter Medium/16px

## Animations
Motion should feel purposeful and efficient, reinforcing the professional nature while adding subtle delight. Animations should be quick and functional, avoiding playfulness in favor of smooth, confident transitions that guide attention.

- **Purposeful Meaning**: Dialog appearances use gentle scale and fade to feel natural, card hover states lift slightly to indicate interactivity, tab transitions slide smoothly to show spatial relationships
- **Hierarchy of Movement**: Primary CTAs have subtle hover lift, expense items animate on delete for clear feedback, budget progress bars animate on load to draw attention to status

## Component Selection
- **Components**: 
  - Dialog (login form, expense add/edit)
  - Card (stat cards, budget cards, expense items)
  - Tabs (expenses/budgets/trends navigation)
  - Button (primary actions, secondary actions)
  - Input (text fields for amounts, descriptions)
  - Select (category dropdown)
  - Alert (over-budget warnings)
  - Table/List (expense history)
  - Progress (budget usage indicators)
  
- **Customizations**: 
  - Custom logo component for BitflowNova branding
  - Currency formatter for INR with ₹ symbol
  - Custom chart components using recharts
  - Stat cards with trend indicators
  
- **States**: 
  - Buttons: Default, hover (lift + brightness), active (pressed), disabled (reduced opacity)
  - Inputs: Default, focus (cyan ring), error (red border), filled
  - Cards: Default, hover (subtle elevation), selected
  
- **Icon Selection**: Phosphor icons for consistent geometric style - Wallet, Plus, ChartBar, Tag, SignOut, User, Pencil, Trash
  
- **Spacing**: Consistent 4px base unit - gaps use gap-4, gap-6, gap-8; padding uses p-4, p-6, p-8; margins minimal with grid/flex gaps preferred
  
- **Mobile**: 
  - Single column layout on mobile (< 768px)
  - Full-width cards stack vertically
  - Tabs remain horizontal with text hidden on small screens, icons only
  - Dialog fills viewport on mobile
  - Stats cards stack in single column
  - Bottom-aligned primary action button for thumb reachability
