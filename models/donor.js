import { DataTypes, UUIDV4 } from 'sequelize';
import sequelize from '../lib/db.js';

// Define the Donor model
const Donor = sequelize.define(
  'Donor',
  {
    id: {
      type: DataTypes.UUID,
      defaultValue: UUIDV4,
      primaryKey: true,
      allowNull: false,
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

// Associations – will be called from a central model index after all models are loaded
Donor.associate = (models) => {
  if (models.Donation) {
    Donor.hasMany(models.Donation, { foreignKey: 'donor_id', as: 'donations' });
  }
};

export default Donor;
