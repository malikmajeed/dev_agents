import { DataTypes } from 'sequelize';
import db from '../lib/db.js';

// Define the Donor model
const Donor = db.define(
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
  },
  {
    tableName: 'donors',
    timestamps: true,
    underscored: true,
  }
);

// Associations can be defined later when related models exist
// Example: Donor.hasMany(models.Donation, { foreignKey: 'donor_id' });

export default Donor;
