export interface Country { code: string; name_ar: string; name_en: string }
export interface Region { id: string; name_ar: string; name_en: string; inferred: boolean }
export interface Place { name_ar: string; name_en: string; type: "city" | "district"; region_id: string }

export interface ParsedAddress {
  input: string;
  cleaned: string;
  normalized: string;
  language: "ar" | "en" | "mixed" | "unknown";
  country_code: string | null;
  region: string | null;
  city: string | null;
  district: string | null;
  street: string | null;
  secondary_street: string | null;
  building: string | null;
  floor: number | null;
  apartment: string | null;
  block: string | null;
  landmark: string | null;
  postal_code: string | null;
  phone: string | null;
  short_address: string | null;
  unparsed: string[];
  warnings: string[];
  confidence: number;
  resolved: { country: Country | null; region: Region | null; city: Place | null; district: Place | null };
}

export function clean(text: string | null | undefined): string;
export function key(text: string | null | undefined, stripArticle?: boolean): string;
export const normalize: typeof key;
export function parse(text: string | null | undefined, options?: { defaultCountry?: string | null }): ParsedAddress;
export function formatAddress(parsed: ParsedAddress, lang?: "ar" | "en"): string;
export function similarity(a: string, b: string): number;
export function isSameAddress(a: string, b: string, threshold?: number): boolean;
export const version: string;
