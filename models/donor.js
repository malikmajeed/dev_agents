import db from '../lib/db.js';
import { DataTypes } from 'sequelize';

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
    // Timestamps are added automatically by Sequelize when `timestamps: true`
  },
  {
    tableName: 'donors',
    timestamps: true,
    underscored: true,
  }
);

// Associations – will be called from a central association loader after all models are imported
Donor.associate = (models) => {
  // A donor can have many donations (assuming a Donation model exists)
  if (models.Donation) {
    Donor.hasMany(models.Donation, {
      foreignKey: 'donor_id',
      as: 'donations',
    });
  }
};

export default Donor;
