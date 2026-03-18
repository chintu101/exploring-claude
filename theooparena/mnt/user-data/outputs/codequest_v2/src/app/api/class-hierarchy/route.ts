import { NextResponse } from "next/server";
import { TraceService } from "@/lib/services/TraceService";

export async function GET() {
  return NextResponse.json({ hierarchy: TraceService.getClassHierarchy() });
}
