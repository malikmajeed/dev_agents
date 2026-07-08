import { DataTypes } from "sequelize";
import db from "../lib/db.js";

// Donor model definition
// Represents an individual who can make donations to the NGO.
// Fields are kept minimal for now; additional attributes can be added later.
const Donor = db.define(
  "Donor",
  {
    id: {
      type: DataTypes.UUID,
      defaultValue: DataTypes.UUIDV4,
      primaryKey: true,
    },
    fullName: {
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
      defaultValue: 0,
    },
  },
  {
    tableName: "donors",
    timestamps: true,
    underscored: true,
  }
);

export default Donor;
