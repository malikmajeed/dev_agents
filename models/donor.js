import { DataTypes } from 'sequelize';
import { sequelize } from '../lib/db';

// Donor model definition
// Represents an individual who can make donations to the NGO.
// Fields are kept minimal for the core donor management feature.
const Donor = sequelize.define(
  'Donor',
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
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
    // Tracks the cumulative amount donated by this donor.
    totalDonated: {
      type: DataTypes.DECIMAL(12, 2),
      allowNull: false,
      defaultValue: 0.0,
    },
  },
  {
    tableName: 'donors',
    timestamps: true,
    underscored: true,
  }
);

// Association placeholder – actual association is set in services or index file.
// Example: Donor.hasMany(models.Donation, { foreignKey: 'donor_id' });

export default Donor;
