import Link from "next/link";

const links = [["/", "Overview"], ["/matches", "Matches"], ["/players", "Players"], ["/analytics", "Analytics"]] as const;

export function Navigation() {
  return <aside className="sidebar"><Link className="brand" href="/">FA<span>•</span>FA</Link><nav aria-label="Primary navigation">{links.map(([href, label]) => <Link key={href} href={href}>{label}</Link>)}</nav><p className="environment">Development<br />scaffold</p></aside>;
}
