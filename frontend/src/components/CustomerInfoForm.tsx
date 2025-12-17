import React, { useState } from 'react';
import './CustomerInfoForm.css';

interface FormField {
  name: string;
  label: string;
  type: string;
  required: boolean;
  placeholder?: string;
  min?: number;
  max?: number;
  step?: number;
  options?: Array<{ value: string; label: string }>;
}

interface FormData {
  form_type: string;
  title: string;
  description: string;
  fields: FormField[];
  submit_text: string;
}

interface CustomerInfoFormProps {
  formData: FormData;
  onSubmit: (data: Record<string, any>) => void;
  isLoading?: boolean;
}

const CustomerInfoForm: React.FC<CustomerInfoFormProps> = ({
  formData,
  onSubmit,
  isLoading = false,
}) => {
  const [values, setValues] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleChange = (name: string, value: any) => {
    setValues(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    formData.fields.forEach(field => {
      const value = values[field.name];
      
      if (field.required && (!value || value.toString().trim() === '')) {
        newErrors[field.name] = `${field.label} is required`;
        return;
      }

      if (value) {
        // Type-specific validations
        if (field.type === 'number') {
          const numValue = Number(value);
          if (isNaN(numValue)) {
            newErrors[field.name] = `${field.label} must be a valid number`;
          } else {
            if (field.min !== undefined && numValue < field.min) {
              newErrors[field.name] = `${field.label} must be at least ${field.min}`;
            }
            if (field.max !== undefined && numValue > field.max) {
              newErrors[field.name] = `${field.label} must be at most ${field.max}`;
            }
          }
        }

        if (field.type === 'tel' && field.name === 'phone') {
          const phoneRegex = /^[6-9]\d{9}$/;
          if (!phoneRegex.test(value.toString().replace(/\D/g, ''))) {
            newErrors[field.name] = 'Please enter a valid 10-digit mobile number';
          }
        }

        if (field.type === 'text' && field.name === 'full_name') {
          if (value.toString().trim().length < 2) {
            newErrors[field.name] = 'Name must be at least 2 characters long';
          }
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      // Format the data for submission
      const formattedData = {
        form_type: formData.form_type,
        form_data: values,
        timestamp: new Date().toISOString(),
      };
      
      onSubmit(formattedData);
    }
  };

  const renderField = (field: FormField) => {
    const baseClassName = `form-field ${errors[field.name] ? 'error' : ''}`;
    
    switch (field.type) {
      case 'select':
        return (
          <div key={field.name} className={baseClassName}>
            <label htmlFor={field.name}>{field.label} {field.required && '*'}</label>
            <select
              id={field.name}
              value={values[field.name] || ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              required={field.required}
              disabled={isLoading}
            >
              <option value="">Select {field.label}</option>
              {field.options?.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {errors[field.name] && <span className="error-text">{errors[field.name]}</span>}
          </div>
        );

      case 'number':
        return (
          <div key={field.name} className={baseClassName}>
            <label htmlFor={field.name}>{field.label} {field.required && '*'}</label>
            <input
              id={field.name}
              type="number"
              placeholder={field.placeholder}
              value={values[field.name] || ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              min={field.min}
              max={field.max}
              step={field.step}
              required={field.required}
              disabled={isLoading}
            />
            {errors[field.name] && <span className="error-text">{errors[field.name]}</span>}
          </div>
        );

      case 'tel':
        return (
          <div key={field.name} className={baseClassName}>
            <label htmlFor={field.name}>{field.label} {field.required && '*'}</label>
            <input
              id={field.name}
              type="tel"
              placeholder={field.placeholder}
              value={values[field.name] || ''}
              onChange={(e) => {
                // Format phone number input
                const value = e.target.value.replace(/\D/g, '').slice(0, 10);
                handleChange(field.name, value);
              }}
              required={field.required}
              disabled={isLoading}
            />
            {errors[field.name] && <span className="error-text">{errors[field.name]}</span>}
          </div>
        );

      default:
        return (
          <div key={field.name} className={baseClassName}>
            <label htmlFor={field.name}>{field.label} {field.required && '*'}</label>
            <input
              id={field.name}
              type={field.type}
              placeholder={field.placeholder}
              value={values[field.name] || ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              required={field.required}
              disabled={isLoading}
            />
            {errors[field.name] && <span className="error-text">{errors[field.name]}</span>}
          </div>
        );
    }
  };

  return (
    <div className="customer-info-form">
      <form onSubmit={handleSubmit}>
        <h2 className="form-title">{formData.title}</h2>
        
        <p className="form-description">{formData.description}</p>

        <div className="form-grid">
          {formData.fields.map((field) => renderField(field))}
        </div>

        <div className="form-submit">
          <button
            type="submit"
            className="submit-button"
            disabled={isLoading}
          >
            {isLoading ? 'Processing...' : formData.submit_text}
          </button>
        </div>

        <p className="security-note">
          🔒 Your information is secure and will be used only for loan processing
        </p>
      </form>
    </div>
  );
};

export default CustomerInfoForm;