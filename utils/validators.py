from typing import Iterable, Optional
import re

def normalize_str(v: Optional[str]) -> str:
	if v is None:
		return ""
	return str(v).strip()


def normalize_org_type(v: Optional[str]) -> str:
	"""Return a canonical org_type (lowercase). Map common variants to 'ndpb'."""
	v = normalize_str(v).lower()
	if v in {"ndpb", "ndpbs", "n.d.p.b", "n d p b"}:
		return "ndpb"
	return v


def normalize_relationship_type(v: Optional[str]) -> str:
	return normalize_str(v).lower()


def normalize_node_type(v: Optional[str]) -> str:
	"""Normalize a variety of node type names to canonical values."""
	v = normalize_str(v).lower()
	mapping = {
		"organisation": "organisation",
		"organization": "organisation",
		"org": "organisation",
		"stakeholder": "stakeholder",
		"person": "stakeholder",
		"painpoint": "painpoint",
		"pain_point": "painpoint",
		"commercial": "commercial",
		"procurement": "commercial",
		"commercials": "commercial",
	}
	return mapping.get(v, v)


def is_valid_relationship_type(v: str, allowed: Iterable[str]) -> bool:
	return normalize_str(v).lower() in {a.lower() for a in allowed}


def safe_rel_filter_list(filters: Iterable[str], allowed: Iterable[str]) -> list:
	"""Return a sanitized, lowercased list of relationship filters limited to allowed values."""
	allowed_set = {a.lower() for a in allowed}
	out = []
	for f in filters or []:
		fv = normalize_str(f).lower()
		if fv in allowed_set:
			out.append(fv)
	return out


def parse_budget(value) -> Optional[float]:
	try:
		if value is None:
			return None
		if isinstance(value, (int, float)):
			return float(value)
		s = str(value).replace(",", "").strip()
		# allow currency symbols
		s = re.sub(r"[^0-9.\-]", "", s)
		return float(s)
	except Exception:
		return None


def is_positive_int(value) -> bool:
	try:
		return int(value) >= 0
	except Exception:
		return False

