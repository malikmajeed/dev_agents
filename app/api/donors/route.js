import { getAllDonors, createDonor } from '../../../services/donorService.js';
import { z } from 'zod';
import jwt from 'jsonwebtoken';

// Validation schema for a donor
const donorSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  phone: z.string().optional(),
  address: z.string().optional(),
});

// Helper to extract Bearer token
function getToken(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) return null;
  return authHeader.split(' ')[1];
}

// Verify JWT and return payload (throws on failure)
async function verifyAuth(request) {
  const token = getToken(request);
  if (!token) throw new Error('Missing authentication token');
  const secret = process.env.JWT_SECRET;
  if (!secret) throw new Error('JWT secret not configured');
  try {
    const payload = jwt.verify(token, secret);
    return payload;
  } catch (e) {
    throw new Error('Invalid authentication token');
  }
}

export async function GET(request) {
  try {
    await verifyAuth(request);
    const donors = await getAllDonors();
    return new Response(JSON.stringify(donors), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (err) {
    const status = err.message.includes('Missing') || err.message.includes('Invalid') ? 401 : 500;
    return new Response(JSON.stringify({ error: err.message }), {
      status,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

export async function POST(request) {
  try {
    await verifyAuth(request);
    const body = await request.json();
    const parsed = donorSchema.parse(body);
    const donor = await createDonor(parsed);
    return new Response(JSON.stringify(donor), {
      status: 201,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (err) {
    const status = err instanceof z.ZodError ? 400 : (err.message.includes('Missing') || err.message.includes('Invalid') ? 401 : 500);
    return new Response(JSON.stringify({ error: err.message }), {
      status,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
