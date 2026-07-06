import { DataTypes, Model } from "sequelize";
import db from "../lib/db.js";
import bcrypt from "bcryptjs";

class Donor extends Model {
  /**
   * Compare a plain password with the stored hash.
   * @param {string} password
   * @returns {Promise<boolean>}
   */
  async verifyPassword(password) {
    if (!this.password) return false;
    return bcrypt.compare(password, this.password);
  }

  /**
   * Set a plain password; it will be hashed before persisting.
   * @param {string} plainPassword
   */
  setPassword(plainPassword) {
    this._plainPassword = plainPassword;
  }
}

Donor.init(
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
    // Stores the bcrypt hash of the donor's password (if authentication is needed)
    password: {
      type: DataTypes.STRING,
      allowNull: true,
    },
  },
  {
    sequelize: db,
    modelName: "Donor",
    tableName: "donors",
    timestamps: true,
    hooks: {
      beforeCreate: async (donor) => {
        if (donor._plainPassword) {
          donor.password = await bcrypt.hash(donor._plainPassword, 10);
        }
      },
      beforeUpdate: async (donor) => {
        if (donor._plainPassword) {
          donor.password = await bcrypt.hash(donor._plainPassword, 10);
        }
      },
    },
  }
);

export default Donor;
