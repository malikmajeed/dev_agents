import { DataTypes } from 'sequelize';
import db from '../lib/db.js';

// Donor model definition
// Represents an individual donor in the system.
// Fields include basic contact information and timestamps.
const Donor = db.define('Donor', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true,
  },
  firstName: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  lastName: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  email: {
    type: DataTypes.STRING,
    allowNull: false,
    unique: true,
    validate: {
      isEmail: true,
    },
  },
  phone: {
    type: DataTypes.STRING,
    allowNull: true,
  },
  address: {
    type: DataTypes.TEXT,
    allowNull: true,
  },
}, {
  tableName: 'donors',
  timestamps: true,
  underscored: true,
});

export default Donor;
