import { DataTypes, Model } from 'sequelize';
import db from '../lib/db.js';
import bcrypt from 'bcryptjs';

class Donor extends Model {
  /**
   * Verify a plain text password against the stored hash.
   * @param {string} password
   * @returns {Promise<boolean>}
   */
  async verifyPassword(password) {
    return bcrypt.compare(password, this.passwordHash);
  }
}

Donor.init(
  {
    id: {
      type: DataTypes.UUID,
      primaryKey: true,
      defaultValue: DataTypes.UUIDV4,
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
    // Virtual field used only for setting a password; it hashes into passwordHash.
    password: {
      type: DataTypes.VIRTUAL,
      set(value) {
        // Store the plain password temporarily (not persisted)
        this.setDataValue('password', value);
        // Hash and store in passwordHash
        const hash = bcrypt.hashSync(value, 10);
        this.setDataValue('passwordHash', hash);
      },
      validate: {
        len: [6, 100], // enforce reasonable length
      },
    },
    passwordHash: {
      type: DataTypes.STRING,
      allowNull: false,
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
    sequelize: db,
    modelName: 'Donor',
    tableName: 'donors',
    timestamps: true,
    // By default omit the password hash from JSON responses
    defaultScope: {
      attributes: { exclude: ['passwordHash'] },
    },
    // Scope to include the hash when needed (e.g., auth checks)
    scopes: {
      withPassword: { attributes: {} },
    },
  }
);

export default Donor;
