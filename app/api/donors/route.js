import { NextResponse } from 'next/server';
import { createDonor, getAllDonors } from '@/services/donorService';
import { z } from 'zod';

// Validation schema for creating a donor
const donorSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional(),
  address: z.string().optional(),
});

/**
 * GET /api/donors
 * Returns a list of all donors.
 */
export async function GET(request) {
  try {
    const donors = await getAllDonors();
    return NextResponse.json({ success: true, data: donors });
  } catch (error) {
    console.error('Error fetching donors:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch donors' },
      { status: 500 }
    );
  }
}

/**
 * POST /api/donors
 * Creates a new donor record.
 */
export async function POST(request) {
  try {
    const body = await request.json();
    const validation = donorSchema.safeParse(body);

    if (!validation.success) {
      const errors = validation.error.errors.map((e) => ({
        path: e.path,
        message: e.message,
      }));
      return NextResponse.json(
        { success: false, error: 'Validation failed', details: errors },
        { status: 400 }
      );
    }

    const donor = await createDonor(validation.data);
    return NextResponse.json({ success: true, data: donor }, { status: 201 });
  } catch (error) {
    console.error('Error creating donor:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to create donor' },
      { status: 500 }
    );
  }
}
