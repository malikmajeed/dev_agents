import { getAllDonors, createDonor } from '@/services/donorService';
import { z } from 'zod';
import jwt from 'jsonwebtoken';

// Validation schema for creating a donor
const donorSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  phone: z.string().optional(),
  address: z.string().optional(),
});

/**
 * Verify JWT token from Authorization header.
 * Returns the decoded payload if valid, otherwise null.
 */
function verifyToken(req) {
  const authHeader = req.headers.get('authorization');
  if (!authHeader) return null;
  const parts = authHeader.split(' ');
  if (parts.length !== 2) return null;
  const token = parts[1];
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET);
    return payload;
  } catch (e) {
    return null;
  }
}

export async function GET(req) {
  const user = verifyToken(req);
  if (!user) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), {
      status: 401,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  try {
    const donors = await getAllDonors();
    return new Response(JSON.stringify(donors), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (err) {
    console.error('GET /api/donors error:', err);
    return new Response(JSON.stringify({ error: 'Failed to fetch donors' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

export async function POST(req) {
  const user = verifyToken(req);
  if (!user) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), {
      status: 401,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  try {
    const body = await req.json();
    const parsed = donorSchema.safeParse(body);
    if (!parsed.success) {
      return new Response(
        JSON.stringify({
          error: 'Invalid request data',
          details: parsed.error.errors,
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    const donor = await createDonor(parsed.data);
    return new Response(JSON.stringify(donor), {
      status: 201,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (err) {
    console.error('POST /api/donors error:', err);
    return new Response(JSON.stringify({ error: 'Failed to create donor' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
