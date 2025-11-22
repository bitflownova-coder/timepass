# Planning Guide

A personal finance tracker that helps users monitor expenses, set category budgets, and visualize spending patterns to make informed financial decisions.

**Experience Qualities**:
1. **Trustworthy** - Clear, accurate data presentation with no surprises; users should feel confident their financial information is properly tracked and secure.
2. **Insightful** - Transforms raw expense data into actionable insights through visual trends and budget comparisons that reveal spending habits.
3. **Effortless** - Quick expense entry and intuitive navigation make daily financial tracking feel like a natural habit rather than a chore.

**Complexity Level**: Light Application (multiple features with basic state)
  - Multiple interconnected features (expenses, budgets, trends) with persistent state management but no authentication or complex data relationships.

## Essential Features

### Expense Logging
- **Functionality**: Add, edit, and delete expense entries with amount, category, description, and date
- **Purpose**: Capture spending data as the foundation for all financial insights
- **Trigger**: Click "Add Expense" button or quick-add action
- **Progression**: Click add → Fill form (amount, category, description, date) → Submit → See expense in list with visual confirmation
- **Success criteria**: Expenses persist between sessions, display correctly in list, and can be edited/deleted without errors

### Budget Management
- **Functionality**: Set monthly budget limits for different spending categories
- **Purpose**: Establish spending guardrails and enable budget vs. actual comparisons
- **Trigger**: Navigate to "Budgets" section
- **Progression**: View categories → Set/edit budget amount → Save → See budget reflected in spending overview with progress indicators
- **Success criteria**: Budgets persist, display remaining/overspent amounts accurately, and update in real-time as expenses change

### Spending Trends Visualization
- **Functionality**: View spending over time with charts showing category breakdowns and monthly trends
- **Purpose**: Reveal spending patterns and help identify areas for financial improvement
- **Trigger**: Navigate to "Trends" or "Overview" section
- **Progression**: Open trends view → See chart with current month data → Filter by category or time period → Identify patterns
- **Success criteria**: Charts update dynamically with expense changes, display accurate totals, and render smoothly on all screen sizes

### Category Management
- **Functionality**: Organize expenses into predefined categories (Food, Transport, Entertainment, Shopping, Bills, Health, Other)
- **Purpose**: Enable meaningful grouping and analysis of spending patterns
- **Trigger**: Select category when adding/editing expense
- **Progression**: Create expense → Choose from category list → Expense tagged with category → Category appears in reports
- **Success criteria**: All expenses have categories, categories display consistently, and budget tracking works per category

## Edge Case Handling

- **Empty States**: First-time users see helpful onboarding messages prompting them to add their first expense or set a budget
- **Negative Amounts**: System prevents negative expense amounts through form validation
- **Future Dates**: Allow future-dated expenses for planned spending but indicate them visually
- **Budget Exceeded**: Display clear visual warnings (red indicators) when spending exceeds category budgets
- **No Data Periods**: When viewing trends for periods with no expenses, show empty state message rather than broken charts
- **Large Numbers**: Format currency values with proper thousand separators and maintain precision for cents
- **Deletion Confirmation**: Require confirmation before deleting expenses or budgets to prevent accidental data loss

## Design Direction

The design should feel trustworthy and professional yet approachable - like a capable financial advisor who's also a friend. A clean, minimal interface that emphasizes clarity over decoration, with purposeful use of color to communicate financial health (green for under budget, red for overspent). The interface should be data-rich but never overwhelming.

## Color Selection

Complementary palette with financial health indicators
- **Primary Color**: Deep Navy Blue (oklch(0.25 0.05 250)) - Communicates trust, stability, and professionalism; used for primary actions and headers
- **Secondary Colors**: 
  - Soft Slate (oklch(0.45 0.02 250)) for secondary UI elements and muted backgrounds
  - Light Blue Gray (oklch(0.96 0.01 250)) for cards and subtle containers
- **Accent Color**: Vibrant Teal (oklch(0.65 0.15 200)) - Highlights interactive elements and calls-to-action; energetic but not aggressive
- **Financial Indicators**:
  - Success Green (oklch(0.65 0.18 145)) for under-budget and positive trends
  - Warning Amber (oklch(0.75 0.15 85)) for approaching budget limits
  - Alert Red (oklch(0.60 0.22 25)) for over-budget situations
- **Foreground/Background Pairings**:
  - Background (Light Blue Gray #F7F8FA): Dark Navy text (oklch(0.25 0.05 250)) - Ratio 8.9:1 ✓
  - Card (White #FFFFFF): Dark Navy text (oklch(0.25 0.05 250)) - Ratio 10.5:1 ✓
  - Primary (Deep Navy oklch(0.25 0.05 250)): White text (#FFFFFF) - Ratio 10.5:1 ✓
  - Secondary (Soft Slate oklch(0.45 0.02 250)): White text (#FFFFFF) - Ratio 5.2:1 ✓
  - Accent (Vibrant Teal oklch(0.65 0.15 200)): White text (#FFFFFF) - Ratio 4.9:1 ✓
  - Success (Green oklch(0.65 0.18 145)): White text (#FFFFFF) - Ratio 4.7:1 ✓

## Font Selection

Professional yet friendly typography that balances precision (for numbers) with readability (for labels and descriptions); Inter font family for its excellent number legibility and modern appearance.

- **Typographic Hierarchy**:
  - H1 (Page Title): Inter SemiBold / 32px / -0.02em letter spacing / 1.2 line height
  - H2 (Section Header): Inter SemiBold / 24px / -0.01em letter spacing / 1.3 line height
  - H3 (Card Title): Inter Medium / 18px / normal letter spacing / 1.4 line height
  - Body (Default text): Inter Regular / 15px / normal letter spacing / 1.6 line height
  - Caption (Meta info): Inter Regular / 13px / normal letter spacing / 1.4 line height
  - Numbers (Currency): Inter SemiBold / contextual size / tabular-nums font feature
  - Button: Inter Medium / 14px / normal letter spacing / 1 line height

## Animations

Subtle and functional with occasional moments of delight - animations should guide attention to important financial updates (budget warnings, successful saves) while keeping the interface feeling responsive and alive without distracting from financial data.

- **Purposeful Meaning**: Use gentle scale and fade animations to confirm expense additions; pulse effect on budget warnings to draw attention to overspending
- **Hierarchy of Movement**: 
  - Primary: Chart transitions and data updates (smooth, informative)
  - Secondary: Card hover states and button interactions (immediate feedback)
  - Tertiary: List item additions/deletions (contextual understanding)

## Component Selection

- **Components**: 
  - Dialog for expense add/edit forms (modal focus on data entry)
  - Card for expense items, budget categories, and stat summaries
  - Tabs for navigation between Expenses, Budgets, and Trends sections
  - Select for category dropdowns
  - Input for amount/description fields with proper number formatting
  - Calendar (date-picker) for expense dates
  - Progress bar for budget consumption visualization
  - Table for expense list with sortable columns
  - Badge for category tags and status indicators
  - Alert for budget warnings and informational messages
  - Recharts for spending trend visualizations (bar/line charts)

- **Customizations**: 
  - Custom expense list component with inline edit/delete actions
  - Budget progress card showing spent/remaining with color-coded indicators
  - Category icon mapping (using Phosphor icons)
  - Summary stat cards with large numbers and trend indicators

- **States**: 
  - Buttons: Subtle shadow on hover, slight scale down (0.98) on active, disabled state with reduced opacity
  - Inputs: Blue border glow on focus, red border for validation errors, green checkmark for valid
  - Cards: Subtle lift (shadow increase) on hover, border highlight for interactive cards
  - Progress bars: Smooth width transitions, color changes at thresholds (50% warning, 100% danger)

- **Icon Selection**: 
  - Plus (Add expense)
  - Wallet (Budget/Finance)
  - TrendUp/TrendDown (Spending trends)
  - PencilSimple (Edit)
  - Trash (Delete)
  - ChartBar (Analytics/Trends)
  - Tag (Categories)
  - Calendar (Date selection)
  - Category-specific: Hamburger (Food), Car (Transport), FilmSlate (Entertainment), ShoppingBag (Shopping), Receipt (Bills), FirstAid (Health), DotsThree (Other)

- **Spacing**: 
  - Card padding: p-6 (24px)
  - Section gaps: gap-6 (24px)
  - List item spacing: gap-3 (12px)
  - Form field spacing: gap-4 (16px)
  - Page margins: px-4 md:px-8 (16px mobile, 32px desktop)

- **Mobile**: 
  - Tabs convert to bottom navigation bar on mobile
  - Expense table becomes stacked cards showing key info
  - Dialog forms stack inputs vertically with full-width buttons
  - Charts adjust aspect ratio for portrait orientation
  - Add expense button becomes floating action button (FAB) in bottom right
  - Summary stats stack vertically instead of grid layout
