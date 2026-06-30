import { Sequelize } from 'sequelize';

const globalForDb = globalThis;

function createSequelize() {
  const url = process.env.DATABASE_URL;
  if (!url) {
    return null;
  }
  return new Sequelize(url, {
    dialect: 'postgres',
    logging: false,
    dialectOptions: process.env.NODE_ENV === 'production'
      ? { ssl: { require: true, rejectUnauthorized: false } }
      : {},
  });
}

const sequelize = globalForDb.sequelize ?? createSequelize();

if (process.env.NODE_ENV !== 'production' && sequelize) {
  globalForDb.sequelize = sequelize;
}

export default sequelize;
