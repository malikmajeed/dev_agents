import { createDonor, getAllDonors } from '../../services/donorService';
import { z } from 'zod';

const donorSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  phone: z.string().optional(),
  address: z.string().optional(),
});

export async function GET(request) {
  try {
    const donors = await getAllDonors();
    return new Response(JSON.stringify({ success: true, data: donors }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('GET donors error:', error);
    return new Response(JSON.stringify({ success: false, error: 'Failed to fetch donors' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

export async function POST(request) {
  try {
    const body = await request.json();
    const parsed = donorSchema.safeParse(body);
    if (!parsed.success) {
      return new Response(
        JSON.stringify({
          success: false,
          error: 'Invalid request data',
          details: parsed.error.format(),
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    const newDonor = await createDonor(parsed.data);
    return new Response(JSON.stringify({ success: true, data: newDonor }), {
      status: 201,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('POST donor error:', error);
    return new Response(JSON.stringify({ success: false, error: 'Failed to create donor' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
