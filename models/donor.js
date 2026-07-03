import { sequelize, DataTypes } from '../lib/db';

// Define the Donor model representing a person who can make donations.
// Fields are kept simple for the MVP; additional attributes can be added later.
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
    // Ensure the JSON representation does not leak any future sensitive fields.
    defaultScope: {
      attributes: { exclude: [] },
    },
  }
);

// Associations – placed here to keep model definitions self‑contained.
// The actual Donation model will be defined elsewhere; this guard avoids runtime errors.
Donor.associate = (models) => {
  if (models.Donation) {
    Donor.hasMany(models.Donation, { foreignKey: 'donorId', as: 'donations' });
  }
};

export default Donor;
