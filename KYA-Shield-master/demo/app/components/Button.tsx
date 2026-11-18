import Link from "next/link";
import type { ButtonHTMLAttributes, MouseEventHandler, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "tertiary" | "outline" | "danger" | "icon" | "navigation";
type ButtonSize = "default" | "sm";

type ButtonProps = {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  href?: string;
  className?: string;
  onClick?: MouseEventHandler<HTMLElement>;
} & Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children" | "className" | "onClick">;

export function Button({
  children,
  variant = "primary",
  size = "default",
  href,
  className = "",
  onClick,
  ...props
}: ButtonProps) {
  const classes = ["k-btn", `k-btn-${variant}`, size === "sm" ? "k-btn-sm" : "", className].filter(Boolean).join(" ");

  if (href) {
    return <Link href={href} className={classes} onClick={onClick}>{children}</Link>;
  }

  return <button {...props} className={classes} onClick={onClick}>{children}</button>;
}
