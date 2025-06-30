/**
 * Enhanced Button Component
 * 
 * Following best practices:
 * - Full accessibility (ARIA, keyboard navigation)
 * - Multiple variants and sizes
 * - Loading and disabled states
 * - Icon support
 * - Proper TypeScript typing
 * - Consistent design system
 */

import React, { ButtonHTMLAttributes, forwardRef, ReactNode } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

const buttonVariants = cva(
  // Base styles
  [
    'inline-flex items-center justify-center gap-2',
    'rounded-md text-sm font-medium transition-all duration-200',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
    'disabled:pointer-events-none disabled:opacity-50',
    'select-none cursor-pointer',
    'active:scale-95',
  ],
  {
    variants: {
      variant: {
        default: [
          'bg-primary text-primary-foreground shadow',
          'hover:bg-primary/90',
          'focus-visible:ring-primary',
        ],
        destructive: [
          'bg-destructive text-destructive-foreground shadow-sm',
          'hover:bg-destructive/90',
          'focus-visible:ring-destructive',
        ],
        outline: [
          'border border-input bg-background shadow-sm',
          'hover:bg-accent hover:text-accent-foreground',
          'focus-visible:ring-ring',
        ],
        secondary: [
          'bg-secondary text-secondary-foreground shadow-sm',
          'hover:bg-secondary/80',
          'focus-visible:ring-secondary',
        ],
        ghost: [
          'hover:bg-accent hover:text-accent-foreground',
          'focus-visible:ring-accent',
        ],
        link: [
          'text-primary underline-offset-4',
          'hover:underline',
          'focus-visible:ring-primary',
        ],
        success: [
          'bg-green-600 text-white shadow',
          'hover:bg-green-700',
          'focus-visible:ring-green-500',
        ],
        warning: [
          'bg-yellow-600 text-white shadow',
          'hover:bg-yellow-700',
          'focus-visible:ring-yellow-500',
        ],
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-10 rounded-md px-8',
        xl: 'h-12 rounded-lg px-10 text-base',
        icon: 'h-9 w-9',
        'icon-sm': 'h-8 w-8',
        'icon-lg': 'h-10 w-10',
      },
      fullWidth: {
        true: 'w-full',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
      fullWidth: false,
    },
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /**
   * Content to render inside the button
   */
  children?: ReactNode;
  
  /**
   * Show loading spinner and disable interaction
   */
  loading?: boolean;
  
  /**
   * Loading text to show when loading is true
   */
  loadingText?: string;
  
  /**
   * Icon to show at the start of the button
   */
  startIcon?: ReactNode;
  
  /**
   * Icon to show at the end of the button
   */
  endIcon?: ReactNode;
  
  /**
   * ARIA label for accessibility
   */
  'aria-label'?: string;
  
  /**
   * Tooltip text
   */
  tooltip?: string;
  
  /**
   * Custom className for additional styling
   */
  className?: string;
  
  /**
   * Button variant
   */
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link' | 'success' | 'warning';
  
  /**
   * Button size
   */
  size?: 'default' | 'sm' | 'lg' | 'xl' | 'icon' | 'icon-sm' | 'icon-lg';
  
  /**
   * Make button full width
   */
  fullWidth?: boolean;
}

/**
 * Enhanced Button component with accessibility and design system support
 */
const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      fullWidth,
      loading = false,
      loadingText,
      startIcon,
      endIcon,
      children,
      disabled,
      type = 'button',
      'aria-label': ariaLabel,
      tooltip,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;
    
    // Determine ARIA label
    const effectiveAriaLabel = ariaLabel || (typeof children === 'string' ? children : undefined);
    
    const buttonContent = (
      <>
        {/* Loading spinner or start icon */}
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : (
          startIcon && (
            <span className="flex-shrink-0" aria-hidden="true">
              {startIcon}
            </span>
          )
        )}
        
        {/* Button text */}
        {children && (
          <span className={cn(
            'flex-1',
            (startIcon || loading || endIcon) && 'mx-1'
          )}>
            {loading && loadingText ? loadingText : children}
          </span>
        )}
        
        {/* End icon (hidden when loading) */}
        {!loading && endIcon && (
          <span className="flex-shrink-0" aria-hidden="true">
            {endIcon}
          </span>
        )}
      </>
    );

    const buttonElement = (
      <button
        className={cn(buttonVariants({ variant, size, fullWidth, className }))}
        ref={ref}
        type={type}
        disabled={isDisabled}
        aria-label={effectiveAriaLabel}
        aria-disabled={isDisabled}
        aria-busy={loading}
        {...props}
      >
        {buttonContent}
      </button>
    );

    // Wrap with tooltip if provided
    if (tooltip) {
      return (
        <div className="relative group">
          {buttonElement}
          <div
            role="tooltip"
            className={cn(
              'absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2',
              'px-2 py-1 text-xs text-white bg-gray-900 rounded',
              'opacity-0 group-hover:opacity-100 transition-opacity duration-200',
              'pointer-events-none whitespace-nowrap z-50'
            )}
          >
            {tooltip}
            <div className="absolute top-full left-1/2 transform -translate-x-1/2">
              <div className="border-4 border-transparent border-t-gray-900" />
            </div>
          </div>
        </div>
      );
    }

    return buttonElement;
  }
);

Button.displayName = 'Button';

export { Button, buttonVariants };

// Export additional button components for common use cases

/**
 * Primary action button
 */
export const PrimaryButton = forwardRef<HTMLButtonElement, Omit<ButtonProps, 'variant'>>(
  (props, ref) => <Button {...props} variant="default" ref={ref} />
);
PrimaryButton.displayName = 'PrimaryButton';

/**
 * Secondary action button
 */
export const SecondaryButton = forwardRef<HTMLButtonElement, Omit<ButtonProps, 'variant'>>(
  (props, ref) => <Button {...props} variant="secondary" ref={ref} />
);
SecondaryButton.displayName = 'SecondaryButton';

/**
 * Destructive action button (for delete, cancel, etc.)
 */
export const DestructiveButton = forwardRef<HTMLButtonElement, Omit<ButtonProps, 'variant'>>(
  (props, ref) => <Button {...props} variant="destructive" ref={ref} />
);
DestructiveButton.displayName = 'DestructiveButton';

/**
 * Icon-only button
 */
export const IconButton = forwardRef<HTMLButtonElement, Omit<ButtonProps, 'size' | 'children'> & {
  icon: ReactNode;
  size?: 'icon' | 'icon-sm' | 'icon-lg';
}>(
  ({ icon, size = 'icon', 'aria-label': ariaLabel, ...props }, ref) => (
    <Button
      {...props}
      size={size}
      aria-label={ariaLabel || 'Icon button'}
      ref={ref}
    >
      {icon}
    </Button>
  )
);
IconButton.displayName = 'IconButton';

/**
 * Link-styled button
 */
export const LinkButton = forwardRef<HTMLButtonElement, Omit<ButtonProps, 'variant'>>(
  (props, ref) => <Button {...props} variant="link" ref={ref} />
);
LinkButton.displayName = 'LinkButton';

/**
 * Success action button
 */
export const SuccessButton = forwardRef<HTMLButtonElement, Omit<ButtonProps, 'variant'>>(
  (props, ref) => <Button {...props} variant="success" ref={ref} />
);
SuccessButton.displayName = 'SuccessButton';

/**
 * Warning action button
 */
export const WarningButton = forwardRef<HTMLButtonElement, Omit<ButtonProps, 'variant'>>(
  (props, ref) => <Button {...props} variant="warning" ref={ref} />
);
WarningButton.displayName = 'WarningButton';

// Usage examples and stories for Storybook
export const buttonExamples = {
  // Basic usage
  basic: () => <Button>Click me</Button>,
  
  // With loading state
  loading: () => <Button loading>Processing...</Button>,
  
  // With icons
  withIcons: () => (
    <div className="space-x-2">
      <Button startIcon={<span>👍</span>}>Like</Button>
      <Button endIcon={<span>→</span>}>Next</Button>
    </div>
  ),
  
  // Different variants
  variants: () => (
    <div className="space-x-2">
      <Button variant="default">Default</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="destructive">Delete</Button>
      <Button variant="success">Success</Button>
      <Button variant="warning">Warning</Button>
    </div>
  ),
  
  // Different sizes
  sizes: () => (
    <div className="space-x-2 items-center flex">
      <Button size="sm">Small</Button>
      <Button size="default">Default</Button>
      <Button size="lg">Large</Button>
      <Button size="xl">Extra Large</Button>
    </div>
  ),
  
  // Icon buttons
  iconButtons: () => (
    <div className="space-x-2">
      <IconButton icon={<span>❤️</span>} aria-label="Like" />
      <IconButton icon={<span>⭐</span>} aria-label="Star" size="icon-sm" />
      <IconButton icon={<span>🔍</span>} aria-label="Search" size="icon-lg" />
    </div>
  ),
  
  // Full width
  fullWidth: () => <Button fullWidth>Full Width Button</Button>,
  
  // With tooltip
  withTooltip: () => <Button tooltip="This is a helpful tooltip">Hover me</Button>,
};

export default Button;