import {
  Anchor,
  Languages,
  Radio,
  ShieldCheck,
} from "lucide-react";

import type { LanguageCode } from "../../types/orca";


interface AppHeaderProps {
  language: LanguageCode;
  onLanguageChange: (language: LanguageCode) => void;
}


export function AppHeader({
  language,
  onLanguageChange,
}: AppHeaderProps) {
  return (
    <header className="app-header">
      <div className="app-header__inner">
        <a
          className="brand"
          href="#top"
          aria-label="ORCA home"
        >
          <span className="brand__icon">
            <Anchor size={24} strokeWidth={2.2} />
          </span>

          <span>
            <strong className="brand__name">ORCA</strong>
            <span className="brand__description">
              Ocean Risk & Catch Advisor
            </span>
          </span>
        </a>

        <div className="app-header__actions">
          <div className="system-status">
            <Radio size={15} aria-hidden="true" />
            <span>Intelligence online</span>
          </div>

          <div className="verification-status">
            <ShieldCheck size={16} aria-hidden="true" />
            Human verified
          </div>

          <label className="language-selector">
            <Languages size={17} aria-hidden="true" />

            <span className="sr-only">
              Interface language
            </span>

            <select
              value={language}
              onChange={(event) => {
                onLanguageChange(
                  event.target.value as LanguageCode,
                );
              }}
              aria-label="Select interface language"
            >
              <option value="en">English</option>
              <option value="hi">हिन्दी</option>
              <option value="or">ଓଡ଼ିଆ</option>
            </select>
          </label>
        </div>
      </div>
    </header>
  );
}