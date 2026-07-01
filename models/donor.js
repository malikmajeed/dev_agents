import { DataTypes } from 'sequelize';
import sequelize from '../lib/db.js';

// Donor model definition
// Represents an individual who can make donations to the NGO.
// Fields include personal contact information and a running total of donations.
const Donor = sequelize.define(
  'Donor',
  {
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
      validate: { isEmail: true },
    },
    phone: {
      type: DataTypes.STRING,
      allowNull: true,
    },
    address: {
      type: DataTypes.TEXT,
      allowNull: true,
    },
    totalDonated: {
      type: DataTypes.DECIMAL(12, 2),
      defaultValue: 0,
    },
  },
  {
    tableName: 'donors',
    timestamps: true,
    underscored: true,
  }
);

export default Donor;
