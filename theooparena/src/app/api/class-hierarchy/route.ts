import { NextResponse } from "next/server";
import { TraceService } from "../../../lib/services/TraceService";

export async function GET() {
  const hierarchy = TraceService.getClassHierarchy();
  const concepts  = TraceService.getConcepts().map(c => ({
    name:        c.name,
    description: c.definition,
    example:     c.codeExample,
  }));
  return NextResponse.json({ hierarchy, concepts });
}
