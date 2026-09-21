import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400/80 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-sky-500 text-zinc-950 hover:bg-sky-400",
        secondary:
          "border border-zinc-700 bg-zinc-900 text-zinc-100 hover:bg-zinc-800",
        ghost: "text-zinc-300 hover:bg-zinc-800 hover:text-zinc-50",
        destructive:
          "border border-red-900/80 bg-red-950/60 text-red-200 hover:bg-red-950",
        link: "text-sky-400 underline-offset-4 hover:text-sky-300 hover:underline",
      },
      size: {
        default: "h-9 px-3 py-2",
        sm: "h-8 px-2.5 text-xs",
        lg: "h-10 px-4",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants>;

export function Button({ className, variant, size, type = "button", ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  );
}
