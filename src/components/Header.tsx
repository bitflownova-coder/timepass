import { Button } from '@/components/ui/button'
import { SignOut, User, Moon, Sun } from '@phosphor-icons/react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useTheme } from '@/hooks/use-theme'

interface HeaderProps {
  userEmail: string
  onLogout: () => void
}

export function Header({ userEmail, onLogout }: HeaderProps) {
  const { theme, toggleTheme } = useTheme()

  return (
    <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary">
              <div className="text-lg font-bold text-primary-foreground tracking-tighter">
                <span className="text-accent text-sm">Bit</span>
              </div>
            </div>
            <div>
              <h1 className="text-xl font-semibold text-foreground">BitflowNova</h1>
              <p className="text-xs text-muted-foreground">Expense Management</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={toggleTheme}
              className="gap-2"
            >
              {theme === 'light' ? (
                <>
                  <Moon weight="duotone" className="w-4 h-4" />
                  <span className="hidden sm:inline">Dark</span>
                </>
              ) : (
                <>
                  <Sun weight="duotone" className="w-4 h-4" />
                  <span className="hidden sm:inline">Light</span>
                </>
              )}
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2">
                  <User weight="duotone" className="w-4 h-4" />
                  <span className="hidden sm:inline">{userEmail.split('@')[0]}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col gap-1">
                    <p className="text-sm font-medium">Signed in as</p>
                    <p className="text-xs text-muted-foreground">{userEmail}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={onLogout} className="gap-2 text-destructive focus:text-destructive">
                  <SignOut className="w-4 h-4" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </header>
  )
}
